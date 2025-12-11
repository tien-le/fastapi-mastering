"""Logging configuration module."""
import logging
from logging.config import dictConfig

from app.core.config import DevConfig, settings

logger = logging.getLogger(__name__)


def obfuscated(email: str, obfuscated_length: int) -> str:
    """test.mail@gmail.com --> te*******@gmail.com
    """
    characters = email[:obfuscated_length]
    first, last = email.split("@")
    return f'{characters}{"*" * (len(first)-obfuscated_length)}@{last}'


class EmailObfuscationFilter(logging.Filter):

    def __init__(self, name: str="", obfuscated_length: int=2) -> None:
        super().__init__(name)
        self.obfuscated_length = obfuscated_length

    def filter(self, record: logging.LogRecord) -> bool:
        if "email" in record.__dict__:
            record.email = obfuscated(record.email, self.obfuscated_length)
        return True


def configure_logging() -> None:
    """Configure application logging with correlation ID support.

    Sets up:
    - Console handler with Rich formatting (development)
    - Rotating file handler for persistent logs
    - Logtail handler for cloud logging (if API key is configured)
    - Correlation ID filtering for request tracking
    - Environment-specific log levels
    """
    # Base handlers that are always included
    handlers = {
        "console_handler": {
            # "class": "logging.StreamHandler",
            "class": "rich.logging.RichHandler",
            "level": "DEBUG",
            "formatter": "console_formatter",
            "filters": ["correlation_id", "email_obfuscation"],
        },
        "rotating_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "file_formatter",
            "filename": "var/app.log",
            "maxBytes": 1024 * 1024 * 1,  # 1MB
            "backupCount": 5,  # 5 files
            "encoding": "utf8",
            "filters": ["correlation_id", "email_obfuscation"],
        },
    }

    # Base handler list for loggers
    base_handlers = ["console_handler", "rotating_file"]
    all_handlers = base_handlers[:]

    # Add Logtail handler if API key is configured
    if settings.LOGTAIL_API_KEY and isinstance(settings, DevConfig):
        logger.debug("Adding LogTail")
        handlers["logtail"] = {
            "class": "logtail.LogtailHandler",
            "level": "DEBUG",
            "formatter": "file_formatter",  # Use JSON formatter for structured logging
            "filters": ["correlation_id", "email_obfuscation"],
            "source_token": settings.LOGTAIL_API_KEY,
        }
        all_handlers.append("logtail")

    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "filters": {
                "correlation_id": {
                    "()": "asgi_correlation_id.CorrelationIdFilter",
                    "uuid_length": 8 if isinstance(settings, DevConfig) else 32,
                    "default_value": "-",
                },
                "email_obfuscation": {
                    "()": EmailObfuscationFilter,
                    "obfuscated_length": 2 if isinstance(settings, DevConfig) else 0
                }
            },
            "formatters": {
                "console_formatter": {
                    "class": "logging.Formatter",
                    "datefmt": "%Y-%m-%dT%H:%M:%S",
                    "format": "(%(correlation_id)s) %(name)s:%(lineno)d - %(message)s",
                },
                "file_formatter": {
                    # "class": "logging.Formatter",
                    # "format": "%(asctime)s.%(msecs)03dZ | %(levelname)-8s | [%(correlation_id)s] %(name)s:%(lineno)d - %(message)s",
                    # Example: 2025-12-07T14:40:47.638Z | INFO     | [6484f906] app.routers.post:81 - Creating new post with body length: 33

                    "datefmt": "%Y-%m-%dT%H:%M:%S",
                    "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
                    "format": "%(asctime)s %(msecs)03dZ %(levelname)-8s %(correlation_id)s %(name)s %(lineno)d %(message)s",
                    # Example: {"asctime": "2025-12-07T14:57:54", "msecs": 884.0, "levelname": "INFO", "correlation_id": "-", "name": "uvicorn.error", "lineno": 62, "message": "Application startup complete."}
                },
            },
            "handlers": handlers,
            "loggers": {
                "uvicorn": {
                    "handlers": all_handlers,
                    "level": "INFO",
                },
                "app": {
                    "handlers": all_handlers,
                    "level": "DEBUG" if isinstance(settings, DevConfig) else "INFO",
                    "propagate": False,
                },
                "databases": {
                    "handlers": base_handlers,
                    "level": "WARNING",
                },
                "aiosqlite": {
                    "handlers": base_handlers,
                    "level": "WARNING",
                },
            },
        }
    )
