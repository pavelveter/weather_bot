#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

import uvicorn
from web_app import app


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
