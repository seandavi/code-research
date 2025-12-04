"""Configuration settings for the LinkML Schema Manager."""
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Database
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{BASE_DIR}/schemas.db")

# Storage
SCHEMA_STORAGE_DIR = Path(os.getenv("SCHEMA_STORAGE_DIR", BASE_DIR / "schema_storage"))
SCHEMA_STORAGE_DIR.mkdir(exist_ok=True, parents=True)

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", str(BASE_DIR / "app.log"))

# API Settings
API_TITLE = "LinkML Schema Manager"
API_VERSION = "0.1.0"
API_DESCRIPTION = """
FastAPI-based LinkML schema manager, validator, and toolkit.

## Features

* **Schema Management**: Upload, version, and manage LinkML schemas
* **Schema Functionality**: Generate code, Excel templates from schemas
* **Validation**: Validate data files against schemas
* **Logging**: Track all requests and responses
"""
