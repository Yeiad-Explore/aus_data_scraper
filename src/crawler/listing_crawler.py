"""Crawler for visa listing page."""

import structlog
from playwright.async_api import Page

from config.settings import Settings

logger = structlog.get_logger()


class ListingCrawler:
    """Crawls the main visa listing page.

    This crawler loads the visa listing page and returns the raw HTML
    after waiting for JavaScript hydration and lazy loading.
    """

    def __init__(self, settings: Settings):
        """Initialize listing crawler.

        Args:
            settings: Application settings
        """
        self.settings = settings

    async def crawl(self, page: Page) -> str:
        """Crawl the visa listing page and return raw HTML.

        Args:
            page: Playwright page instance

        Returns:
            Raw HTML content of the listing page

        Raises:
            PlaywrightError: If page load fails
        """
        logger.info("crawling_listing_page", url=self.settings.ENTRY_URL)

        # Navigate to listing page
        await page.goto(self.settings.ENTRY_URL, wait_until="networkidle")
        await page.wait_for_load_state("domcontentloaded")

        # Wait for main content to load
        # This selector may need adjustment based on actual page structure
        try:
            await page.wait_for_selector("main", timeout=10000)
        except Exception as e:
            logger.warning("main_content_wait_failed", error=str(e))

        # Scroll to trigger lazy loading
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(2000)

        # Get HTML content
        html = await page.content()

        logger.info("listing_page_crawled", html_length=len(html))

        return html
