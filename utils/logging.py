"""Logging configuration using loguru."""

from loguru import logger
from config.settings import settings
import sys


def setup_logging():
    """Configure loguru logger with appropriate settings."""
    
    # Remove default handler
    logger.remove()
    
    # Add console handler with formatting
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.log_level,
        colorize=True
    )
    
    # Add file handler for production
    if settings.environment == "production":
        logger.add(
            "logs/dataroles_{time:YYYY-MM-DD}.log",
            rotation="00:00",
            retention="30 days",
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
        )
    
    logger.info(f"Logging initialized at {settings.log_level} level")
