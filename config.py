#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os

from dotenv import load_dotenv


load_dotenv()

# Telegram Bot Token
TG_KEY = os.getenv("TG_KEY")
if not TG_KEY:
    raise RuntimeError("Не найден TG_KEY в .env")

# OpenWeatherMap API Key
OWM_KEY = os.getenv("OPENWEATHER_API_KEY")
if not OWM_KEY:
    raise RuntimeError("Не найден OPENWEATHER_API_KEY в .env")

# Default city
DEFAULT_CITY = "Saint Petersburg"

# OpenWeatherMap API base URL
BASE_URL = "https://api.openweathermap.org/data/2.5"

# HTTP timeout settings
HTTP_TIMEOUT_SEC = 10.0
HTTP_CONNECT_TIMEOUT_SEC = 5.0

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()],
)
log = logging.getLogger("weather-bot")
