#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Any, Dict

from aiogram.utils.text_decorations import html_decoration as hd
from formatters import fmt_pressure


def build_current_message(data: Dict[str, Any]) -> str:
    """Построить сообщение о текущей погоде"""
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
