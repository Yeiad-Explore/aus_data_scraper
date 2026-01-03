"""Crawler for individual visa detail pages."""

import structlog
from playwright.async_api import Page
from tenacity import retry, stop_after_attempt, wait_fixed

from config.settings import Settings

logger = structlog.get_logger()


class DetailCrawler:
    """Crawls individual visa detail pages.

    This crawler loads visa detail pages, expands all collapsible sections,
    and returns the raw HTML after ensuring all content is visible.
    """

    def __init__(self, settings: Settings):
        """Initialize detail crawler.

        Args:
            settings: Application settings
        """
        self.settings = settings

    @retry(stop=stop_after_attempt(2), wait=wait_fixed(3))
    async def crawl(self, page: Page, url: str) -> str:
        """Crawl a visa detail page and return raw HTML.

        This method includes retry logic (1 retry) as per the plan.

        Args:
            page: Playwright page instance
            url: URL of the visa detail page

        Returns:
            Raw HTML content of the visa detail page

        Raises:
            PlaywrightError: If page load fails after retries
        """
        logger.info("crawling_visa_detail", url=url)

        # Navigate to visa detail page
        await page.goto(url, wait_until="networkidle")
        await page.wait_for_load_state("domcontentloaded")

        # Wait for JavaScript hydration
        await self._wait_for_hydration(page)

        # Expand all accordions and collapsible sections
        await self._expand_all_accordions(page)

        # Scroll to trigger any lazy-loaded content
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(1000)

        # Get HTML content
        html = await page.content()

        logger.info("visa_detail_crawled", url=url, html_length=len(html))

        return html

    async def _wait_for_hydration(self, page: Page) -> None:
        """Wait for JavaScript hydration to complete.

        Args:
            page: Playwright page instance
        """
        try:
            # Wait for main content area
            await page.wait_for_selector("main", timeout=10000)
            # Extra wait for React/Vue hydration
            await page.wait_for_timeout(2000)
        except Exception as e:
            logger.warning("hydration_wait_failed", error=str(e))

    async def _expand_all_accordions(self, page: Page) -> None:
        """Click all expandable sections to reveal hidden content.

        This tries multiple common accordion selectors to ensure we catch
        all collapsible content on the page.

        Args:
            page: Playwright page instance
        """
        try:
            # Common accordion/collapse selectors
            accordion_selectors = [
                'button[aria-expanded="false"]',
                '.accordion-button.collapsed',
                '[data-toggle="collapse"]',
                'details:not([open])',
                '.collapse:not(.show)',
            ]

            expanded_count = 0

            for selector in accordion_selectors:
                elements = await page.query_selector_all(selector)

                for element in elements:
                    try:
                        # Check if element is visible and enabled
                        is_visible = await element.is_visible()
                        is_enabled = await element.is_enabled()

                        if is_visible and is_enabled:
                            # For <details> elements, use JavaScript
                            tag_name = await element.evaluate("el => el.tagName.toLowerCase()")
                            if tag_name == "details":
                                await element.evaluate("el => el.open = true")
                            else:
                                await element.click()

                            expanded_count += 1
                            # Small delay to allow content to expand
                            await page.wait_for_timeout(200)

                    except Exception as e:
                        # Ignore errors from individual elements
                        logger.debug("accordion_click_failed", error=str(e))
                        continue

            logger.info("accordions_expanded", count=expanded_count)

        except Exception as e:
            logger.warning("accordion_expansion_failed", error=str(e))
