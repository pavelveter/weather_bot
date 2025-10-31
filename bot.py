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
from fastapi import FastAPI
import httpx
import uvicorn


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
_polling_task: Optional[asyncio.Task] = None


async def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=HTTP_TIMEOUT)
    return _client


# ------------------------------------------------------------------------------
# HELPERS
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


# ------------------------------------------------------------------------------
# WEATHER FETCHERS
# ------------------------------------------------------------------------------

async def fetch_current_weather(city: str, lang: str = "ru") -> Dict[str, Any]:
    client = await get_client()
    params = {"q": city, "appid": OWM_KEY, "units": "metric", "lang": lang}
    r = await client.get(f"{BASE_URL}/weather", params=params)
    r.raise_for_status()
    return r.json()


async def fetch_forecast_3h(city: str, lang: str = "ru") -> Dict[str, Any]:
    client = await get_client()
    params = {"q": city, "appid": OWM_KEY, "units": "metric", "lang": lang, "cnt": 8}
    r = await client.get(f"{BASE_URL}/forecast", params=params)
    r.raise_for_status()
    return r.json()


# ------------------------------------------------------------------------------
# MESSAGE BUILDERS
# ------------------------------------------------------------------------------

def build_current_message(data: Dict[str, Any]) -> str:
    weather = data["weather"][0]["description"]
    temp = data["main"]["temp"]
    hum = data["main"]["humidity"]
    pressure = fmt_pressure(data["main"]["pressure"])
    wind = data["wind"]["speed"]

    return (
        f"{hd.bold('Погода в')} {hd.quote(data['name'])}:\n"
        f"{weather}\n"
        f"🌡 {temp} °C\n"
        f"💧 {hum}%\n"
        f"💨 {wind} м/с\n"
        f"🔽 Давление: {pressure}"
    )


# ------------------------------------------------------------------------------
# TELEGRAM BOT
# ------------------------------------------------------------------------------

bot = Bot(token=TG_KEY, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()
app = FastAPI(title="weather-bot")


async def handle_city(message: Message, city: str):
    try:
        data = await fetch_current_weather(city)
        await message.reply(build_current_message(data))
    except Exception as e:
        await message.reply(f"Ошибка: {e}")


@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.reply("Напиши /weather <город> или просто название города!")


@dp.message(Command("weather"))
async def cmd_weather(message: Message, command: CommandObject):
    city = (command.args or "").strip() or DEFAULT_CITY
    await handle_city(message, city)


@dp.message(F.text)
async def msg_city(message: Message):
    await handle_city(message, message.text)


# ------------------------------------------------------------------------------
# FASTAPI ENDPOINTS (Render health check)
# ------------------------------------------------------------------------------

@app.get("/")
async def root():
    return {"status": "ok", "service": "weather-bot"}


@app.get("/healthz")
async def healthz():
    return {"ok": True}


@app.on_event("startup")
async def on_startup():
    global _polling_task
    _polling_task = asyncio.create_task(
        dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    )


@app.on_event("shutdown")
async def on_shutdown():
    global _polling_task
    if _polling_task:
        _polling_task.cancel()
        try:
            await _polling_task
        except asyncio.CancelledError:
            pass
    if _client:
        await _client.aclose()


# ------------------------------------------------------------------------------
# ENTRYPOINT
# ------------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run("bot:app", host="0.0.0.0", port=port)