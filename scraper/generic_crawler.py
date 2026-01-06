"""
Generic web crawler with smart section detection.
Handles interactive elements and intelligent link discovery.
"""

import asyncio
import logging
from typing import Optional, List, Tuple
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError
from tenacity import retry, stop_after_attempt, wait_fixed

logger = logging.getLogger(__name__)


class GenericCrawler:
    """Crawls web pages with smart section expansion and link discovery."""

    def __init__(self, page: Page):
        """
        Initialize crawler with a Playwright page.

        Args:
            page: Playwright page object
        """
        self.page = page

    @retry(stop=stop_after_attempt(2), wait=wait_fixed(3))
    async def crawl_page(
        self,
        url: str,
        expand_accordions: bool = True,
        accordion_selectors: Optional[List[str]] = None
    ) -> Tuple[str, List[str]]:
        """
        Crawl a single page with interactive element expansion.

        Args:
            url: URL to crawl
            expand_accordions: Whether to expand interactive elements
            accordion_selectors: List of CSS selectors for expandable elements

        Returns:
            Tuple of (html_content, expanded_section_selectors)
        """
        logger.info(f"Crawling page: {url}")

        try:
            # Navigate to the page
            await self.page.goto(url, wait_until="domcontentloaded", timeout=30000)

            # Wait for network to be idle
            await self.page.wait_for_load_state("networkidle", timeout=10000)

            # Wait for Vue/React/Angular content to render
            # Look for common content containers
            try:
                await self.page.wait_for_selector(
                    ".tiles-container, .tile, main, [class*='content']",
                    timeout=5000
                )
            except Exception:
                pass  # Continue even if selector not found

            # Additional buffer for JavaScript hydration
            await asyncio.sleep(3)

            expanded_selectors = []

            if expand_accordions:
                expanded_selectors = await self._expand_all_sections(accordion_selectors)

            # Scroll to trigger lazy loading
            await self._scroll_page()

            # Get the final HTML
            html = await self.page.content()

            logger.info(f"Successfully crawled {url} ({len(html)} bytes, {len(expanded_selectors)} sections expanded)")
            return html, expanded_selectors

        except PlaywrightTimeoutError as e:
            logger.error(f"Timeout crawling {url}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error crawling {url}: {e}")
            raise

    async def _expand_all_sections(self, selectors: Optional[List[str]] = None) -> List[str]:
        """
        Expand all interactive sections on the page.

        Args:
            selectors: List of CSS selectors for expandable elements

        Returns:
            List of selectors that were successfully expanded
        """
        if selectors is None:
            selectors = [
                "button[aria-expanded='false']",
                ".accordion-button.collapsed",
                "[data-toggle='collapse']",
                "details:not([open])",
                ".collapse:not(.show)",
                "[role='tab'][aria-selected='false']",
            ]

        expanded = []

        for selector in selectors:
            try:
                elements = await self.page.query_selector_all(selector)

                if not elements:
                    continue

                logger.debug(f"Found {len(elements)} elements matching '{selector}'")

                for element in elements:
                    try:
                        # Check if it's a details element (special handling)
                        tag_name = await element.evaluate("el => el.tagName.toLowerCase()")

                        if tag_name == "details":
                            # For details elements, set open attribute
                            await element.evaluate("el => el.open = true")
                            expanded.append(selector)
                        else:
                            # For buttons/other elements, click them
                            # Check if visible and enabled
                            is_visible = await element.is_visible()
                            is_enabled = await element.is_enabled()

                            if is_visible and is_enabled:
                                await element.click()
                                # Wait a bit for content to load
                                await asyncio.sleep(0.3)
                                expanded.append(selector)

                    except Exception as e:
                        logger.debug(f"Could not expand element with '{selector}': {e}")
                        continue

            except Exception as e:
                logger.debug(f"Error with selector '{selector}': {e}")
                continue

        logger.info(f"Expanded {len(expanded)} interactive sections")
        return list(set(expanded))  # Deduplicate

    async def _scroll_page(self):
        """Scroll the page to trigger lazy loading."""
        try:
            # Scroll to bottom
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(0.5)

            # Scroll back to top
            await self.page.evaluate("window.scrollTo(0, 0)")
            await asyncio.sleep(0.3)

        except Exception as e:
            logger.debug(f"Error scrolling page: {e}")

    async def click_tab(self, selector: str) -> bool:
        """
        Click a specific tab element.

        Args:
            selector: CSS selector for the tab

        Returns:
            True if successfully clicked
        """
        try:
            element = await self.page.query_selector(selector)
            if element:
                await element.click()
                await asyncio.sleep(0.5)  # Wait for content to load
                return True
        except Exception as e:
            logger.debug(f"Could not click tab '{selector}': {e}")

        return False

    async def get_tab_content(self, tab_selector: str, content_selector: str) -> Optional[str]:
        """
        Click a tab and get its content.

        Args:
            tab_selector: CSS selector for the tab button
            content_selector: CSS selector for the content area

        Returns:
            HTML content of the tab panel
        """
        try:
            # Click the tab
            if await self.click_tab(tab_selector):
                # Wait for content to appear
                await self.page.wait_for_selector(content_selector, timeout=5000)

                # Get the content
                content = await self.page.inner_html(content_selector)
                return content

        except Exception as e:
            logger.debug(f"Could not get tab content: {e}")

        return None

    async def extract_all_tabs(
        self,
        tab_container_selector: str,
        tab_selector: str = "[role='tab']"
    ) -> List[dict]:
        """
        Extract content from all tabs in a tab group.

        Args:
            tab_container_selector: CSS selector for the tab container
            tab_selector: CSS selector for individual tabs

        Returns:
            List of dicts with {name, content} for each tab
        """
        tabs_data = []

        try:
            # Find all tabs
            tabs = await self.page.query_selector_all(f"{tab_container_selector} {tab_selector}")

            if not tabs:
                logger.debug(f"No tabs found with selector: {tab_container_selector} {tab_selector}")
                return tabs_data

            logger.info(f"Found {len(tabs)} tabs to extract")

            for i, tab in enumerate(tabs):
                try:
                    # Get tab name
                    tab_name = await tab.inner_text()

                    # Click the tab
                    await tab.click()
                    await asyncio.sleep(0.5)

                    # Get associated content panel
                    # Try to find aria-controls attribute
                    panel_id = await tab.get_attribute("aria-controls")

                    if panel_id:
                        panel = await self.page.query_selector(f"#{panel_id}")
                        if panel:
                            content = await panel.inner_html()
                            tabs_data.append({
                                "name": tab_name.strip(),
                                "content": content
                            })
                    else:
                        # Fallback: get the active tab panel
                        panel = await self.page.query_selector("[role='tabpanel']:not([hidden])")
                        if panel:
                            content = await panel.inner_html()
                            tabs_data.append({
                                "name": tab_name.strip(),
                                "content": content
                            })

                except Exception as e:
                    logger.debug(f"Could not extract tab {i}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error extracting tabs: {e}")

        return tabs_data
