#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta, timezone
from typing import Optional


def wind_dir_from_deg(deg: Optional[float]) -> str:
    """Преобразует градусы направления ветра в буквенное обозначение"""
    if deg is None:
        return "-"
    dirs = [
        "N",
        "NNE",
        "NE",
        "ENE",
        "E",
        "ESE",
        "SE",
        "SSE",
        "S",
        "SSW",
        "SW",
        "WSW",
        "W",
        "WNW",
        "NW",
        "NNW",
    ]
    idx = int((deg % 360) / 22.5 + 0.5) % 16
    return dirs[idx]


def fmt_pressure(hpa: Optional[float]) -> str:
    """Форматирует давление в гПа и мм рт. ст."""
    if hpa is None:
        return "-"
    mmhg = hpa * 0.75006
    return f"{hpa:.0f} гПа ({mmhg:.0f} мм рт. ст.)"


def fmt_visibility(meters: Optional[int]) -> str:
    """Форматирует видимость в километрах"""
    if meters is None:
        return "-"
    return f"{meters / 1000:.1f} км"


def unix_to_local_time(ts: Optional[int], tz_offset_sec: Optional[int]) -> str:
    """Преобразует Unix timestamp в локальное время с учетом часового пояса"""
    if ts is None:
        return "-"
    offset = timezone(timedelta(seconds=tz_offset_sec or 0))
    dt = datetime.fromtimestamp(ts, tz=offset)
    return dt.strftime("%H:%M")
