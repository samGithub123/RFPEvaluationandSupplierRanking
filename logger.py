# -*- coding: utf-8 -*-
"""
logger.py - Central logging configuration for the RFP Evaluation project.

What it is for:
    Provide a single place that configures Python logging so every step of
    the pipeline writes a consistent, timestamped record to a file and the
    console. Call get_logger(__name__) from any module to opt in.

What it does:
    ✅ Configures file + console handlers once.
    ✅ Returns named loggers for clear traceability.
"""

import logging
import os

LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rfp_evaluation.log")

_configured = False


def get_logger(name):
    """Return a named logger with the shared file + console configuration."""
    global _configured
    if not _configured:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            handlers=[
                logging.FileHandler(LOG_PATH, encoding="utf-8"),
                logging.StreamHandler(),
            ],
        )
        _configured = True
    return logging.getLogger(name)
