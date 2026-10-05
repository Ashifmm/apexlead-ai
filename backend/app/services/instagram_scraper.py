# Compatibility layer / alias for instagram_scanner.py
from app.services.instagram_scanner import (
    InstagramIntentScanner,
    instagram_scanner,
    HIGH_VOLUME_TAGS,
)

InstagramScraper = InstagramIntentScanner
instagram_scraper = instagram_scanner

__all__ = [
    "InstagramIntentScanner",
    "InstagramScraper",
    "instagram_scanner",
    "instagram_scraper",
    "HIGH_VOLUME_TAGS",
]

