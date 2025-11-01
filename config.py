#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os

from dotenv import load_dotenv


load_dotenv()

# Setup logging (настраиваем раньше, чтобы использовать в определении WEBHOOK_URL)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()],
)
log = logging.getLogger("weather-bot")

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

# Webhook URL (для получения обновлений от Telegram)
# Пытаемся получить автоматически из переменных окружения платформы
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
if not WEBHOOK_URL:
    # Render предоставляет RENDER_EXTERNAL_URL
    render_url = os.getenv("RENDER_EXTERNAL_URL")
    if render_url:
        WEBHOOK_URL = f"{render_url}/webhook"
        log.info(f"Используется RENDER_EXTERNAL_URL: {WEBHOOK_URL}")
    else:
        # Railway предоставляет RAILWAY_PUBLIC_DOMAIN
        railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN")
        if railway_domain:
            WEBHOOK_URL = f"https://{railway_domain}/webhook"
            log.info(f"Используется RAILWAY_PUBLIC_DOMAIN: {WEBHOOK_URL}")
        else:
            raise RuntimeError(
                "Не найден WEBHOOK_URL или переменные окружения платформы "
                "(RENDER_EXTERNAL_URL, RAILWAY_PUBLIC_DOMAIN). "
                "Установите WEBHOOK_URL в .env"
            )

# HTTP timeout settings
HTTP_TIMEOUT_SEC = 10.0
HTTP_CONNECT_TIMEOUT_SEC = 5.0
