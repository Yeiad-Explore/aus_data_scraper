"""Generic Web Scraper - A flat, dependency-free scraper package."""

from .generic_scraper import GenericScraper
from .models import JobConfig, CrawlConfig, GenericPageData, EnrichedPageData, CrawlResult
from .settings import Settings

__all__ = [
    "GenericScraper",
    "JobConfig",
    "CrawlConfig",
    "GenericPageData",
    "EnrichedPageData",
    "CrawlResult",
    "Settings",
]
