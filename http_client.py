#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional

from config import HTTP_CONNECT_TIMEOUT_SEC, HTTP_TIMEOUT_SEC
import httpx


HTTP_TIMEOUT = httpx.Timeout(HTTP_TIMEOUT_SEC, connect=HTTP_CONNECT_TIMEOUT_SEC)
_client: Optional[httpx.AsyncClient] = None


async def get_client() -> httpx.AsyncClient:
    """Получить или создать HTTP клиент (singleton)"""
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=HTTP_TIMEOUT)
    return _client


async def close_client():
    """Закрыть HTTP клиент"""
    global _client
    if _client:
        await _client.aclose()
        _client = None
