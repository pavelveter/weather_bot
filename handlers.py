#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from aiogram.filters import CommandObject
from aiogram.types import Message
from config import DEFAULT_CITY, log
from message_builders import build_current_message
from weather_api import fetch_current_weather


async def handle_city(message: Message, city: str):
    """Обработать запрос погоды для указанного города"""
    try:
        data = await fetch_current_weather(city)
        await message.reply(build_current_message(data))
    except Exception as e:
        log.error(f"Ошибка при получении погоды для {city}: {e}", exc_info=True)
        await message.reply(f"Ошибка: {e}")


async def cmd_start(message: Message):
    """Обработчик команды /start"""
    await message.reply("Напиши /weather <город> или просто название города!")


async def cmd_weather(message: Message, command: CommandObject):
    """Обработчик команды /weather"""
    city = (command.args or "").strip() or DEFAULT_CITY
    await handle_city(message, city)


async def msg_city(message: Message):
    """Обработчик текстовых сообщений (название города)"""
    await handle_city(message, message.text)
