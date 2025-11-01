#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Any, Dict

from config import BASE_URL, OWM_KEY
from http_client import get_client


async def fetch_current_weather(city: str, lang: str = "ru") -> Dict[str, Any]:
    """Получить текущую погоду для указанного города"""
    client = await get_client()
    params = {"q": city, "appid": OWM_KEY, "units": "metric", "lang": lang}
    r = await client.get(f"{BASE_URL}/weather", params=params)
    r.raise_for_status()
    return r.json()


async def fetch_forecast_3h(city: str, lang: str = "ru") -> Dict[str, Any]:
    """Получить прогноз погоды на 3 часа для указанного города"""
    client = await get_client()
    params = {"q": city, "appid": OWM_KEY, "units": "metric", "lang": lang, "cnt": 8}
    r = await client.get(f"{BASE_URL}/forecast", params=params)
    r.raise_for_status()
    return r.json()
