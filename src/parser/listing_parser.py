"""Parser for generic listing page DOM."""

import re
from typing import List

import structlog
from bs4 import BeautifulSoup

from src.models.listing import ContentListing
from src.utils.url_utils import normalize_url

logger = structlog.get_logger()


class ListingParser:
    """Parses listing page DOM to extract content links.

    This parser extracts links from a listing page using DOM parsing.
    """

    def __init__(self, base_url: str, link_pattern: str = None):
        """Initialize listing parser.

        Args:
            base_url: Base URL for normalizing relative links
            link_pattern: Optional regex pattern to filter links (e.g., "/visas/")
        """
        self.base_url = base_url
        self.link_pattern = link_pattern

    def parse(self, html: str) -> List[ContentListing]:
        """Extract all content links from listing page HTML.

        Args:
            html: Raw HTML content from listing page

        Returns:
            List of ContentListing objects
        """
        soup = BeautifulSoup(html, "lxml")
        items = self._parse_from_dom(soup)

        logger.info("listing_parsed", item_count=len(items))

        return items

    def _parse_from_dom(self, soup: BeautifulSoup) -> List[ContentListing]:
        """Extract content links by parsing DOM.

        Args:
            soup: BeautifulSoup object of the page

        Returns:
            List of ContentListing objects extracted from DOM
        """
        items = []
        links = soup.find_all("a", href=True)

        for link in links:
            href = link.get("href", "").strip()

            if not href:
                continue

            # Apply link pattern filter if specified
            if self.link_pattern and not re.search(self.link_pattern, href):
                continue

            item = self._parse_link(link)
            if item and item.url not in [i.url for i in items]:
                items.append(item)

        return items

    def _parse_link(self, link) -> ContentListing | None:
        """Parse a link element to extract metadata.

        Args:
            link: BeautifulSoup link element

        Returns:
            ContentListing object or None if parsing fails
        """
        try:
            href = link.get("href", "").strip()

            # Remove anchors and query parameters for normalization
            clean_href = href.split("#")[0].split("?")[0]
            # Remove trailing slash for consistency
            clean_href = clean_href.rstrip("/")

            # Normalize URL
            url = normalize_url(clean_href, self.base_url)

            # Get title from link text
            title = link.get_text(strip=True)

            # Skip if no text
            if not title:
                return None

            # Try to find category by looking at parent elements
            category = self._extract_category(link)

            return ContentListing(
                category=category,
                title=title,
                url=url,
            )

        except Exception as e:
            logger.debug("link_parsing_failed", error=str(e))
            return None

    def _extract_category(self, link) -> str:
        """Extract category by looking at parent section headings.

        Args:
            link: BeautifulSoup link element

        Returns:
            Category name or empty string
        """
        # Look for nearest heading before this link
        current = link

        for _ in range(10):  # Limit search depth
            current = current.find_previous(["h2", "h3", "h4"])
            if current:
                text = current.get_text(strip=True)
                if text:
                    return text

        return ""
