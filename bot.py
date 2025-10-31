#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
from datetime import datetime, timedelta, timezone
import logging
import os
from typing import Any, Dict, Optional

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from aiogram.utils.text_decorations import html_decoration as hd
from dotenv import load_dotenv
import httpx


# ------------------------------------------------------------------------------
# CONFIG & LOGGING
# ------------------------------------------------------------------------------

load_dotenv()
TG_KEY = os.getenv("TG_KEY")
OWM_KEY = os.getenv("OPENWEATHER_API_KEY")
DEFAULT_CITY = "Saint Petersburg"

if not TG_KEY:
    raise RuntimeError("Не найден TG_KEY в .env")
if not OWM_KEY:
    raise RuntimeError("Не найден OPENWEATHER_API_KEY в .env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()],
)
log = logging.getLogger("weather-bot")

# ------------------------------------------------------------------------------
# HTTP CLIENT
# ------------------------------------------------------------------------------

HTTP_TIMEOUT = httpx.Timeout(10.0, connect=5.0)
BASE_URL = "https://api.openweathermap.org/data/2.5"
_client: Optional[httpx.AsyncClient] = None


async def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=HTTP_TIMEOUT)
    return _client


# ------------------------------------------------------------------------------
# FORMAT HELPERS
# ------------------------------------------------------------------------------

def wind_dir_from_deg(deg: Optional[float]) -> str:
    if deg is None:
        return "-"
    dirs = [
        "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
        "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"
    ]
    idx = int((deg % 360) / 22.5 + 0.5) % 16
    return dirs[idx]


def fmt_pressure(hpa: Optional[float]) -> str:
    if hpa is None:
        return "-"
    mmhg = hpa * 0.75006
    return f"{hpa:.0f} гПа ({mmhg:.0f} мм рт. ст.)"


def fmt_visibility(meters: Optional[int]) -> str:
    if meters is None:
        return "-"
    return f"{meters / 1000:.1f} км"


def unix_to_local_time(ts: Optional[int], tz_offset_sec: Optional[int]) -> str:
    if ts is None:
        return "-"
    offset = timezone(timedelta(seconds=tz_offset_sec or 0))
    dt = datetime.fromtimestamp(ts, tz=offset)
    return dt.strftime("%H:%M")


def fmt_weather_line(w: Dict[str, Any], tz_offset: int) -> str:
    dt_s = unix_to_local_time(w.get("dt"), tz_offset)
    main = w.get("main", {})
    wind = w.get("wind", {})
    weather_list = w.get("weather") or []
    desc = weather_list[0]["description"] if weather_list else "—"
    temp = main.get("temp")
    feels = main.get("feels_like")
    ws = wind.get("speed")
    wg = wind.get("gust")
    wd = wind_dir_from_deg(wind.get("deg"))

    t = f"{temp:.0f}°C" if isinstance(temp, (int, float)) else "-"
    f = f"{feels:.0f}°C" if isinstance(feels, (int, float)) else "-"
    wind_str = f"{ws:.1f} м/с" if isinstance(ws, (int, float)) else "-"
    if isinstance(wg, (int, float)):
        wind_str += f" (порывы до {wg:.1f})"

    return f"{hd.bold(dt_s)}: {desc}, t={t}, ощущ={f}, ветер {wind_str} {wd}"


# ------------------------------------------------------------------------------
# OPENWEATHER API
# ------------------------------------------------------------------------------

async def fetch_current_weather(city: str, lang: str = "ru") -> Dict[str, Any]:
    client = await get_client()
    params = {"q": city, "appid": OWM_KEY, "units": "metric", "lang": lang}
    log.info(f"Fetching current weather for {city!r}")
    r = await client.get(f"{BASE_URL}/weather", params=params)
    r.raise_for_status()
    return r.json()


async def fetch_forecast_3h(city: str, lang: str = "ru") -> Dict[str, Any]:
    client = await get_client()
    params = {"q": city, "appid": OWM_KEY, "units": "metric", "lang": lang, "cnt": 16}
    log.info(f"Fetching forecast for {city!r}")
    r = await client.get(f"{BASE_URL}/forecast", params=params)
    r.raise_for_status()
    return r.json()


# ------------------------------------------------------------------------------
# MESSAGE BUILDERS
# ------------------------------------------------------------------------------

def build_current_message(payload: Dict[str, Any]) -> str:
    name = hd.quote(payload.get("name") or "—")
    sys = payload.get("sys", {})
    tz_offset = payload.get("timezone", 0)

    weather_list = payload.get("weather") or []
    desc = weather_list[0]["description"] if weather_list else "—"

    main = payload.get("main", {})
    wind = payload.get("wind", {})
    clouds = payload.get("clouds", {})
    visibility = payload.get("visibility")
    rain = payload.get("rain", {})
    snow = payload.get("snow", {})

    temp = main.get("temp")
    feels = main.get("feels_like")
    humidity = main.get("humidity")
    pressure = main.get("pressure")
    grnd = main.get("grnd_level")
    sea = main.get("sea_level")

    wind_speed = wind.get("speed")
    wind_gust = wind.get("gust")
    wind_deg = wind.get("deg")

    clouds_all = clouds.get("all")
    rain_1h = rain.get("1h")
    snow_1h = snow.get("1h")

    sunrise = unix_to_local_time(sys.get("sunrise"), tz_offset)
    sunset = unix_to_local_time(sys.get("sunset"), tz_offset)

    lines = [
        f"{hd.bold('Город')}: {name}",
        f"{hd.bold('Погода')}: {desc}",
        f"{hd.bold('Температура')}: {temp:.1f}°C" if isinstance(temp, (int, float)) else f"{hd.bold('Температура')}: -",
        f"{hd.bold('Ощущается как')}: {feels:.1f}°C" if isinstance(feels, (int, float)) else f"{hd.bold('Ощущается как')}: -",
        f"{hd.bold('Влажность')}: {humidity}%" if isinstance(humidity, (int, float)) else f"{hd.bold('Влажность')}: -",
        f"{hd.bold('Давление')}: {fmt_pressure(pressure)}",
    ]

    if isinstance(sea, (int, float)):
        lines.append(f"{hd.bold('Уровень моря')}: {fmt_pressure(sea)}")
    if isinstance(grnd, (int, float)):
        lines.append(f"{hd.bold('Уровень земли')}: {fmt_pressure(grnd)}")

    if isinstance(wind_speed, (int, float)):
        wind_line = f"{hd.bold('Ветер')}: {wind_speed:.1f} м/с {wind_dir_from_deg(wind_deg)}"
        if isinstance(wind_gust, (int, float)):
            wind_line += f" (порывы до {wind_gust:.1f})"
        lines.append(wind_line)
    else:
        lines.append(f"{hd.bold('Ветер')}: -")

    if isinstance(clouds_all, (int, float)):
        lines.append(f"{hd.bold('Облачность')}: {clouds_all}%")

    lines.append(f"{hd.bold('Видимость')}: {fmt_visibility(visibility)}")

    if isinstance(rain_1h, (int, float)):
        lines.append(f"{hd.bold('Осадки (дождь за 1ч)')}: {rain_1h} мм")
    if isinstance(snow_1h, (int, float)):
        lines.append(f"{hd.bold('Осадки (снег за 1ч)')}: {snow_1h} мм")

    lines.append(f"{hd.bold('Восход')}: {sunrise}")
    lines.append(f"{hd.bold('Закат')}: {sunset}")

    return "\n".join(lines)


def build_forecast_message(payload: Dict[str, Any]) -> str:
    city = hd.quote((payload.get("city") or {}).get("name") or "—")
    tz_offset = (payload.get("city") or {}).get("timezone", 0)
    lst = payload.get("list") or []
    window = lst[:8]
    if not window:
        return f"{hd.bold('Прогноз')} для {city}: данных нет."

    lines = [f"{hd.bold('Прогноз на 24 часа')} — {city}"]
    for w in window:
        lines.append("• " + fmt_weather_line(w, tz_offset))
    return "\n".join(lines)


# ------------------------------------------------------------------------------
# AIOGRAM HANDLERS
# ------------------------------------------------------------------------------

dp = Dispatcher()
bot = Bot(token=TG_KEY, default=DefaultBotProperties(parse_mode="HTML"))


async def handle_city_lookup(message: Message, city: str) -> None:
    city = (city or "").strip()
    if not city:
        city = DEFAULT_CITY

    if len(city) < 2 or len(city) > 80:
        await message.reply("Некорректное название города.")
        return

    try:
        current_payload, forecast_payload = await asyncio.gather(
            fetch_current_weather(city),
            fetch_forecast_3h(city),
        )

        current_text = build_current_message(current_payload)
        forecast_text = build_forecast_message(forecast_payload)
        await message.reply(current_text)
        await message.reply(forecast_text)

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            await message.reply(f"Город <b>{hd.quote(city)}</b> не найден.")
        else:
            log.error(f"HTTP error {e.response.status_code}: {e.response.text}")
            await message.reply(f"Ошибка OpenWeather: {e.response.status_code}.")
    except httpx.RequestError as e:
        log.error(f"Request error: {e}")
        await message.reply("Ошибка сети или таймаут при обращении к API.")
    except Exception:
        log.exception("Unexpected error")
        await message.reply("Непредвиденная ошибка при обработке запроса.")


@dp.message(Command("start"))
async def cmd_start(message: Message) -> None:
    city_safe = hd.quote(DEFAULT_CITY)
    greet = (
        f"{hd.bold('Привет!')} Я покажу погоду и краткий прогноз.\n\n"
        f"{hd.bold('Как пользоваться:')}\n"
        f"• /weather — погода в {city_safe}\n"
        f"• /weather &lt;город&gt; — погода в городе\n"
        f"• Просто напишите название города\n"
        f"• /help — справка\n\n"
        f"Погнали: вот сводка по умолчанию ↓"
    )
    await message.reply(greet)
    await handle_city_lookup(message, DEFAULT_CITY)


@dp.message(Command("help"))
async def cmd_help(message: Message) -> None:
    help_text = (
        f"{hd.bold('Команды:')}\n"
        f"/start — приветствие\n"
        f"/help — справка\n"
        f"/weather — погода в {hd.quote(DEFAULT_CITY)}\n"
        f"/weather &lt;город&gt; — погода и прогноз\n\n"
        f"{hd.bold('Советы:')}\n"
        "Пишите города на любом языке. Если городов одноимённых много — добавьте страну: Paris, FR."
    )
    await message.reply(help_text)


@dp.message(Command("weather"))
async def cmd_weather(message: Message, command: CommandObject) -> None:
    arg_city = (command.args or "").strip() if command else ""
    await handle_city_lookup(message, arg_city or DEFAULT_CITY)


@dp.message(F.text.regexp(r"^[A-Za-zА-Яа-яЁё0-9 ,.'’\-()]{2,80}$"))
async def any_city_text(message: Message) -> None:
    await handle_city_lookup(message, message.text or "")


@dp.message()
async def fallback(message: Message) -> None:
    await message.reply("Используй /start, /help или /weather &lt;город&gt;.")


# ------------------------------------------------------------------------------
# ENTRYPOINT
# ------------------------------------------------------------------------------

async def main() -> None:
    log.info("Starting bot polling...")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        if _client is not None:
            await _client.aclose()
        log.info("Bot stopped.")


if __name__ == "__main__":
    asyncio.run(main())
