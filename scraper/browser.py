"""Playwright browser manager with context management."""

from typing import Optional

import structlog
from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from settings import Settings

logger = structlog.get_logger()


class BrowserManager:
    """Manages single browser context for entire crawl session.

    This ensures we maintain a consistent browser context throughout
    the scraping process, which helps with anti-blocking.
    """

    def __init__(self, settings: Settings):
        """Initialize browser manager.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None

    async def __aenter__(self) -> "BrowserManager":
        """Start Playwright and launch browser."""
        self.playwright = await async_playwright().start()

        # Launch browser
        if self.settings.BROWSER_TYPE == "chromium":
            self.browser = await self.playwright.chromium.launch(
                headless=self.settings.HEADLESS
            )
        elif self.settings.BROWSER_TYPE == "firefox":
            self.browser = await self.playwright.firefox.launch(
                headless=self.settings.HEADLESS
            )
        elif self.settings.BROWSER_TYPE == "webkit":
            self.browser = await self.playwright.webkit.launch(
                headless=self.settings.HEADLESS
            )
        else:
            raise ValueError(f"Unknown browser type: {self.settings.BROWSER_TYPE}")

        # Create browser context with realistic settings
        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            extra_http_headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            },
            locale="en-US",
            timezone_id="America/New_York",
        )

        logger.info(
            "browser_started",
            browser_type=self.settings.BROWSER_TYPE,
            headless=self.settings.HEADLESS,
        )

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close browser and stop Playwright."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

        logger.info("browser_stopped")

    async def new_page(self) -> Page:
        """Create a new page with configured timeouts.

        Returns:
            New Playwright page instance

        Raises:
            RuntimeError: If browser context is not initialized
        """
        if not self.context:
            raise RuntimeError("Browser context not initialized. Use 'async with' to start.")

        page = await self.context.new_page()
        page.set_default_timeout(self.settings.PAGE_LOAD_TIMEOUT)
        page.set_default_navigation_timeout(self.settings.NAVIGATION_TIMEOUT)

        return page
