"""Configuration loader module.

This module provides a centralized way to access application settings.
Settings are loaded based on the ENV_STATE environment variable.
"""
from app.core.config import get_settings

settings = get_settings()
