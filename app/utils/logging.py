"""Centralized logging configuration for small Python entry points."""

import logging


def get_logger(name: str) -> logging.Logger:
    """Return a module-level logger configured with a common project format."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    return logging.getLogger(name)
