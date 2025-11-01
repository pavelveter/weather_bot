#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.types import Update
from config import TG_KEY, WEBHOOK_URL, log
from fastapi import FastAPI, Request, Response
from handlers import cmd_start, cmd_weather, msg_city
from http_client import close_client


# Инициализация бота и диспетчера
bot = Bot(token=TG_KEY, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# Регистрация обработчиков
dp.message.register(cmd_start, Command("start"))
dp.message.register(cmd_weather, Command("weather"))
dp.message.register(msg_city, F.text)

# FastAPI приложение
app = FastAPI(title="weather-bot")


@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {"status": "ok", "service": "weather-bot"}


@app.get("/healthz")
async def healthz():
    """Health check эндпоинт"""
    return {"ok": True}


@app.head("/")
async def root_head():
    """HEAD запрос для корневого эндпоинта"""
    return Response(status_code=200)


@app.head("/healthz")
async def healthz_head():
    """HEAD запрос для health check"""
    return Response(status_code=200)


@app.post("/webhook")
async def webhook_handler(request: Request):
    """Обработчик вебхуков от Telegram"""
    try:
        update_data = await request.json()
        update = Update(**update_data)
        await dp.feed_update(bot, update)
        return {"ok": True}
    except Exception as e:
        log.error(f"Ошибка при обработке вебхука: {e}", exc_info=True)
        return {"ok": False, "error": str(e)}, 500


@app.on_event("startup")
async def on_startup():
    """Установка вебхука при старте FastAPI"""
    webhook_info = await bot.get_webhook_info()
    log.info(f"Текущий вебхук: {webhook_info.url}")

    await bot.set_webhook(
        WEBHOOK_URL,
        allowed_updates=dp.resolve_used_update_types(),
    )
    log.info(f"Вебхук установлен: {WEBHOOK_URL}")


@app.on_event("shutdown")
async def on_shutdown():
    """Удаление вебхука и закрытие соединений при завершении FastAPI"""
    await bot.delete_webhook(drop_pending_updates=True)
    log.info("Вебхук удален")
    await close_client()
