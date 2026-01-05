"""
Smart section detection utility.
Identifies structural/navigational elements vs content reference links.
"""

from typing import List, Set, Tuple
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup, Tag
import logging

logger = logging.getLogger(__name__)


class SectionDetector:
    """Detects and categorizes links and interactive elements on a page."""

    # Selectors for structural/navigational elements (should follow these)
    STRUCTURAL_SELECTORS = [
        # Tabs
        "button[data-tab]",
        "a[role='tab']",
        "li[role='tab'] a",
        ".tab-button",
        ".nav-tabs a",

        # Accordions
        "button[aria-expanded]",
        "summary",
        ".accordion-button",
        ".accordion-header button",

        # Section navigation
        "nav.section-nav a",
        ".section-menu a",
        ".sidebar-nav a",
        ".table-of-contents a",

        # Interactive cards/tiles
        ".card.clickable",
        "a.section-card",
        "a.tile",

        # Related sections
        ".next-section a",
        ".related-section a",
        ".sub-section a",
    ]

    # Selectors for elements to ignore (don't follow these)
    IGNORE_SELECTORS = [
        # Footer/header
        "footer a",
        "header a",
        "nav.main-nav a",
        ".site-nav a",

        # Inline content references
        "p a:not(.section-link)",
        "li a:not(.section-link)",
        "td a:not(.section-link)",

        # Utility links
        ".breadcrumb a",
        ".pagination a",
        ".social-media a",
        "a.external-link",
        "a[target='_blank']",

        # Skip links
        "a.skip-link",
        "a[href^='#top']",
        "a[href='#']",
    ]

    def __init__(self, base_url: str, link_filter: str = "same_path", follow_all_links: bool = False):
        """
        Initialize section detector.

        Args:
            base_url: The base URL being scraped
            link_filter: "same_path", "same_domain", or "all"
            follow_all_links: If True, treat ALL links as structural (follow them all)
        """
        self.base_url = base_url
        self.link_filter = link_filter
        self.follow_all_links = follow_all_links
        self.base_parsed = urlparse(base_url)

    def get_expandable_elements(self, soup: BeautifulSoup) -> List[Tuple[Tag, str]]:
        """
        Find all expandable elements (accordions, tabs, details).

        Returns:
            List of (element, selector_type) tuples
        """
        expandable = []

        # Accordions with aria-expanded
        for elem in soup.select("button[aria-expanded='false']"):
            expandable.append((elem, "accordion"))

        # Details elements
        for elem in soup.select("details:not([open])"):
            expandable.append((elem, "details"))

        # Collapsed elements
        for elem in soup.select(".collapse:not(.show)"):
            expandable.append((elem, "collapse"))

        # Tabs (not currently active)
        for elem in soup.select("[role='tab'][aria-selected='false']"):
            expandable.append((elem, "tab"))

        logger.info(f"Found {len(expandable)} expandable elements")
        return expandable

    def is_structural_link(self, link_tag: Tag) -> bool:
        """
        Determine if a link is structural/navigational.

        Args:
            link_tag: BeautifulSoup tag for the link

        Returns:
            True if this is a structural link that should be followed
        """
        # Check if it matches any structural selector
        for selector in self.STRUCTURAL_SELECTORS:
            try:
                # Check if this element or its parent matches
                if link_tag.select(selector) or link_tag.find_parent(selector):
                    return True
                # Check if element itself matches the selector
                if link_tag.name == selector.split('[')[0] or link_tag.get('class'):
                    # Simple matching for common cases
                    if any(cls in str(link_tag.get('class', [])) for cls in
                           ['section', 'tab', 'accordion', 'nav', 'tile', 'card']):
                        return True
            except Exception:
                continue

        # Check for section-like patterns in href
        href = link_tag.get('href', '')
        if any(pattern in href for pattern in ['/section/', '/category/', '/topic/']):
            return True

        # Check for anchor links (same-page sections) - but ONLY if not follow_all_links mode
        # In follow_all_links mode, we want to prioritize actual page links over anchors
        if not self.follow_all_links and href.startswith('#') and len(href) > 1:
            return True

        return False

    def should_ignore_link(self, link_tag: Tag) -> bool:
        """
        Determine if a link should be ignored.

        Args:
            link_tag: BeautifulSoup tag for the link

        Returns:
            True if this link should be ignored
        """
        # Check if it matches any ignore selector
        for selector in self.IGNORE_SELECTORS:
            try:
                if link_tag.find_parent(selector):
                    return True
            except Exception:
                continue

        href = link_tag.get('href', '')

        # Ignore empty or javascript links
        if not href or href == '#' or href.startswith('javascript:'):
            return True

        # Ignore mailto, tel, etc.
        if href.startswith(('mailto:', 'tel:', 'sms:', 'ftp:')):
            return True

        return False

    def should_follow_url(self, url: str) -> bool:
        """
        Determine if a URL should be followed based on link_filter setting.

        Args:
            url: The URL to check

        Returns:
            True if the URL should be followed
        """
        parsed = urlparse(urljoin(self.base_url, url))

        if self.link_filter == "all":
            return True

        if self.link_filter == "same_domain":
            return parsed.netloc == self.base_parsed.netloc

        if self.link_filter == "same_path":
            # Get the parent directory of the base URL
            # For /visas/employing-and-sponsoring-someone/employing-overseas-workers
            # -> /visas/employing-and-sponsoring-someone
            base_path = self.base_parsed.path.rstrip('/')
            # Always use parent directory (assume last part is the page)
            base_path = '/'.join(base_path.split('/')[:-1])

            # Also accept the base path itself
            link_path = parsed.path.rstrip('/')

            return (parsed.netloc == self.base_parsed.netloc and
                   (link_path.startswith(base_path) or link_path == self.base_parsed.path.rstrip('/')))

        return False

    def categorize_links(self, soup: BeautifulSoup) -> Tuple[List[str], List[dict]]:
        """
        Categorize all links on a page.

        Args:
            soup: BeautifulSoup object of the page

        Returns:
            Tuple of (structural_links, referenced_links)
            - structural_links: List of URLs to follow
            - referenced_links: List of dicts with {text, url, context}
        """
        structural_links = []
        referenced_links = []
        seen_urls: Set[str] = set()
        tile_urls: Set[str] = set()

        # FIRST: Find all tile/card links (these are structural)
        tiles_container = soup.find(class_="tiles-container")
        if tiles_container:
            logger.debug("Found tiles-container")
            tiles = tiles_container.find_all(class_="tile")
            logger.debug(f"Found {len(tiles)} tiles in container")

            for tile in tiles:
                tile_link = tile.find('a', href=True)
                if tile_link:
                    href = tile_link.get('href')
                    absolute_url = urljoin(self.base_url, href)
                    logger.debug(f"Found tile link: {absolute_url}")

                    if self.should_follow_url(absolute_url):
                        tile_urls.add(absolute_url)
                        seen_urls.add(absolute_url)
                        structural_links.append(absolute_url)
                        logger.info(f"Added tile link: {absolute_url}")
        else:
            logger.debug("No tiles-container found")

        # Also look for generic card/tile patterns
        for card in soup.select(".card, .tile, [class*='card'], [class*='tile']"):
            card_link = card.find('a', href=True)
            if card_link:
                href = card_link.get('href')
                absolute_url = urljoin(self.base_url, href)

                if absolute_url not in seen_urls and self.should_follow_url(absolute_url):
                    tile_urls.add(absolute_url)
                    seen_urls.add(absolute_url)
                    structural_links.append(absolute_url)
                    logger.debug(f"Card link: {absolute_url}")

        # SECOND: Process all other <a> tags
        for link in soup.find_all('a', href=True):
            href = link.get('href')

            # Skip if should ignore
            if self.should_ignore_link(link):
                continue

            # Convert to absolute URL
            absolute_url = urljoin(self.base_url, href)

            # Skip if already processed (e.g., already in tiles)
            if absolute_url in seen_urls:
                continue
            seen_urls.add(absolute_url)

            # Check if URL should be followed based on filter
            if not self.should_follow_url(absolute_url):
                continue

            # Determine if structural or reference
            # In follow_all_links mode, ALL links are treated as structural
            if self.follow_all_links or self.is_structural_link(link):
                # Skip anchor-only links in follow_all_links mode (they're same-page references)
                parsed_url = urlparse(absolute_url)
                if self.follow_all_links and parsed_url.fragment and not parsed_url.path:
                    # This is a same-page anchor like #section - skip it
                    continue
                structural_links.append(absolute_url)
                logger.debug(f"Structural link: {absolute_url}")
            else:
                # This is a content reference link
                referenced_links.append({
                    "text": link.get_text(strip=True),
                    "url": absolute_url,
                    "context": self._get_link_context(link)
                })
                logger.debug(f"Reference link: {absolute_url}")

        logger.info(f"Categorized {len(structural_links)} structural links, "
                   f"{len(referenced_links)} reference links")

        return structural_links, referenced_links

    def _get_link_context(self, link_tag: Tag) -> str:
        """
        Get the surrounding context for a link.

        Args:
            link_tag: The link element

        Returns:
            Surrounding text context
        """
        # Get parent paragraph or list item
        parent = link_tag.find_parent(['p', 'li', 'td', 'div'])
        if parent:
            text = parent.get_text(strip=True)
            # Limit context length
            if len(text) > 200:
                return text[:200] + "..."
            return text
        return ""
