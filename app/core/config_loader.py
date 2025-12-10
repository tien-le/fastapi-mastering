"""Configuration loader module.

This module provides a centralized way to access application settings.
Settings are loaded based on the ENV_STATE environment variable.
"""
from app.core.config import get_settings, confirm_token_expire_minutes, access_token_expire_minutes

settings = get_settings()

