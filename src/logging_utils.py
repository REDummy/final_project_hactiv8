from __future__ import annotations

import logging
from typing import Final

_LOG_FORMAT: Final[str] = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def configure_logging(log_level: str, app_env: str) -> None:
    level_name = (log_level or "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    root_logger = logging.getLogger()
    if not root_logger.handlers:
        logging.basicConfig(level=level, format=_LOG_FORMAT)
    else:
        root_logger.setLevel(level)

    logging.getLogger(__name__).info(
        "Logging configured",
        extra={"app_env": app_env, "log_level": logging.getLevelName(level)},
    )
