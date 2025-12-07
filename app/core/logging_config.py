from logging.config import dictConfig

from app.core.config import DevConfig
from app.core.config_loader import settings


def configure_logging() -> None:
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "filters": {
                "correlation_id": {
                    "()": "asgi_correlation_id.CorrelationIdFilter",
                    "uuid_length": 8 if isinstance(settings, DevConfig) else 32,
                    "default_value": "-",
                }
            },
            "formatters": {
                "console_formatter": {
                    "class": "logging.Formatter",
                    "datefmt": "%Y-%m-%dT%H:%M:%S",
                    "format": "(%(correlation_id)s) %(name)s:%(lineno)d - %(message)s",
                },
                "file_formatter": {
                    "class": "logging.Formatter",
                    "datefmt": "%Y-%m-%dT%H:%M:%S",
                    "format": "%(asctime)s.%(msecs)03dZ | %(levelname)-8s | [%(correlation_id)s] %(name)s:%(lineno)d - %(message)s",
                },
            },
            "handlers": {
                "console_handler": {
                    # "class": "logging.StreamHandler",
                    "class": "rich.logging.RichHandler",
                    "level": "DEBUG",
                    "formatter": "console_formatter",
                    "filters": ["correlation_id"],
                },
                "rotating_file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "DEBUG",
                    "formatter": "file_formatter",
                    "filename": "var/app.log",
                    "maxBytes": 1024 * 1024 * 1,  # 1MB
                    "backupCount": 5,  # 5 files
                    "encoding": "utf8",
                    "filters": ["correlation_id"],
                },
            },
            "loggers": {
                "uvicorn": {
                    "handlers": ["console_handler", "rotating_file"],
                    "level": "INFO",
                },
                "app": {
                    "handlers": ["console_handler", "rotating_file"],
                    "level": "DEBUG" if isinstance(settings, DevConfig) else "INFO",
                    "propagate": False,
                },
                "databases": {
                    "handlers": ["console_handler", "rotating_file"],
                    "level": "WARNING",
                },
                "aiosqlite": {
                    "handlers": ["console_handler", "rotating_file"],
                    "level": "WARNING",
                },
            },
        }
    )
