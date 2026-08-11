"""
Production Logging & Runtime Diagnostics Module for NeuroSim 2.0
Provides structured log formatting, log file rotation, and diagnostic event tracking.
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
LOG_FILE = os.path.join(LOG_DIR, "neurosim_runtime.log")

_LOGGER: Optional[logging.Logger] = None


def get_logger(name: str = "neurosim") -> logging.Logger:
    """Returns a configured logger instance with standard format and file rotation."""
    global _LOGGER
    if _LOGGER is not None:
        return _LOGGER.getChild(name) if name != "neurosim" else _LOGGER

    os.makedirs(LOG_DIR, exist_ok=True)
    logger = logging.getLogger("neurosim")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not logger.handlers:
        formatter = logging.Formatter(
            fmt="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # File Handler (10MB max, 3 backups)
        file_handler = RotatingFileHandler(
            LOG_FILE, maxBytes=10 * 1024 * 1024, backupCount=3, encoding="utf-8"
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Console Handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    _LOGGER = logger
    return logger.getChild(name) if name != "neurosim" else logger
