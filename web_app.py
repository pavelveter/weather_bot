#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from config import TG_KEY
from fastapi import FastAPI, Response
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

_polling_task: asyncio.Task | None = None


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


@app.on_event("startup")
async def on_startup():
    """Запуск бота при старте FastAPI"""
    global _polling_task
    _polling_task = asyncio.create_task(
        dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    )


@app.on_event("shutdown")
async def on_shutdown():
    """Остановка бота при завершении FastAPI"""
    global _polling_task
    if _polling_task:
        _polling_task.cancel()
        try:
            await _polling_task
        except asyncio.CancelledError:
            pass
    await close_client()
