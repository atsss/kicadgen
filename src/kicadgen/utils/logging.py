"""Logging setup utilities."""

import logging
import sys


def setup_logger(name: str, verbose: bool = False) -> logging.Logger:
    """
    Set up a logger with appropriate verbosity.

    Args:
        name: Logger name (typically __name__)
        verbose: If True, set to DEBUG level; otherwise INFO

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Set level
    level = logging.DEBUG if verbose else logging.INFO
    logger.setLevel(level)

    # Create console handler
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(level)

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    # Add handler to logger
    if not logger.handlers:
        logger.addHandler(handler)

    return logger
