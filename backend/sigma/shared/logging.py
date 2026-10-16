"""structlog: JSON в проде (JSON_LOGS=true), цветная консоль локально."""

import structlog

from sigma.shared.config import settings


def configure_logging() -> None:
    renderer = (
        structlog.processors.JSONRenderer()
        if settings.json_logs
        else structlog.dev.ConsoleRenderer()
    )
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger("INFO"),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
