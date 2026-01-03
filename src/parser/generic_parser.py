"""
Generic HTML parser for extracting structured content from any webpage.
"""

import logging
from typing import List, Optional
from bs4 import BeautifulSoup, Tag, NavigableString
from urllib.parse import urljoin

from src.models.generic import GenericPageData, InteractiveSection, ReferencedLink
from src.utils.section_detector import SectionDetector

logger = logging.getLogger(__name__)


class GenericParser:
    """Parses HTML content and extracts structured data."""

    # Elements to remove before parsing
    JUNK_SELECTORS = [
        "script",
        "style",
        "nav",
        "header",
        "footer",
        ".breadcrumb",
        ".pagination",
        "#cookie-banner",
        ".cookie-notice",
        ".ad",
        ".advertisement",
        "[role='banner']",
        "[role='navigation']",
        "[role='complementary']",
    ]

    def __init__(self, url: str, link_filter: str = "same_path"):
        """
        Initialize parser.

        Args:
            url: The URL being parsed
            link_filter: Link filtering strategy
        """
        self.url = url
        self.section_detector = SectionDetector(url, link_filter)

    def parse(
        self,
        html: str,
        parent_url: Optional[str] = None,
        depth: int = 0,
        content_area_selector: Optional[str] = None
    ) -> GenericPageData:
        """
        Parse HTML and extract structured data.

        Args:
            html: Raw HTML content
            parent_url: Parent page URL (if this is a child page)
            depth: Depth level from start URL
            content_area_selector: Optional CSS selector for main content area

        Returns:
            GenericPageData object
        """
        soup = BeautifulSoup(html, "html.parser")

        # IMPORTANT: Categorize links BEFORE removing junk
        # This ensures we capture all navigation/tile links
        structural_links, referenced_links = self.section_detector.categorize_links(soup)

        # Remove junk elements
        self._remove_junk(soup)

        # Extract title
        title = self._extract_title(soup)

        # Get main content area if selector provided
        if content_area_selector:
            content_area = soup.select_one(content_area_selector)
            if content_area:
                soup = content_area

        # Extract interactive sections (tabs, accordions)
        interactive_sections = self._extract_interactive_sections(soup)

        # Extract main content
        main_content = self._extract_main_content(soup)

        # Convert referenced_links to ReferencedLink objects
        ref_link_objects = [
            ReferencedLink(**link) for link in referenced_links
        ]

        return GenericPageData(
            url=self.url,
            title=title,
            main_content=main_content,
            interactive_sections=interactive_sections,
            referenced_links=ref_link_objects,
            discovered_links=structural_links,
            parent_url=parent_url,
            depth=depth,
        )

    def _remove_junk(self, soup: BeautifulSoup):
        """Remove unwanted elements from the soup."""
        for selector in self.JUNK_SELECTORS:
            for element in soup.select(selector):
                element.decompose()

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title."""
        # Try h1 first
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)

        # Fallback to <title> tag
        title_tag = soup.find("title")
        if title_tag:
            return title_tag.get_text(strip=True)

        return "Untitled"

    def _extract_interactive_sections(self, soup: BeautifulSoup) -> List[InteractiveSection]:
        """
        Extract content from interactive sections (tabs, accordions, etc.).

        Returns:
            List of InteractiveSection objects
        """
        sections = []

        # Extract accordion sections
        sections.extend(self._extract_accordions(soup))

        # Extract details/summary sections
        sections.extend(self._extract_details(soup))

        # Extract tab panels
        sections.extend(self._extract_tabs(soup))

        logger.info(f"Extracted {len(sections)} interactive sections")
        return sections

    def _extract_accordions(self, soup: BeautifulSoup) -> List[InteractiveSection]:
        """Extract accordion sections."""
        sections = []

        # Look for common accordion patterns
        accordion_buttons = soup.select("button[aria-expanded], .accordion-button")

        for button in accordion_buttons:
            try:
                # Get section name from button text
                section_name = button.get_text(strip=True)

                # Find associated content panel
                controls = button.get("aria-controls")
                if controls:
                    panel = soup.find(id=controls)
                    if panel:
                        content = self._extract_text_content(panel)
                        sections.append(InteractiveSection(
                            section_type="accordion",
                            section_name=section_name,
                            content=content,
                            selector=f"#{controls}"
                        ))
                else:
                    # Try to find next sibling that might be the content
                    next_elem = button.find_next_sibling()
                    if next_elem:
                        content = self._extract_text_content(next_elem)
                        sections.append(InteractiveSection(
                            section_type="accordion",
                            section_name=section_name,
                            content=content
                        ))

            except Exception as e:
                logger.debug(f"Error extracting accordion: {e}")
                continue

        return sections

    def _extract_details(self, soup: BeautifulSoup) -> List[InteractiveSection]:
        """Extract details/summary sections."""
        sections = []

        for details in soup.find_all("details"):
            try:
                summary = details.find("summary")
                section_name = summary.get_text(strip=True) if summary else "Details"

                # Get content (everything except the summary)
                if summary:
                    summary.decompose()

                content = self._extract_text_content(details)

                sections.append(InteractiveSection(
                    section_type="details",
                    section_name=section_name,
                    content=content
                ))

            except Exception as e:
                logger.debug(f"Error extracting details: {e}")
                continue

        return sections

    def _extract_tabs(self, soup: BeautifulSoup) -> List[InteractiveSection]:
        """Extract tab panels."""
        sections = []

        # Find tab panels
        tab_panels = soup.select("[role='tabpanel']")

        for panel in tab_panels:
            try:
                # Try to find associated tab button
                panel_id = panel.get("id")
                section_name = "Tab"

                if panel_id:
                    # Find button with aria-controls matching this id
                    tab_button = soup.find("button", {"aria-controls": panel_id})
                    if not tab_button:
                        tab_button = soup.find("a", {"aria-controls": panel_id})

                    if tab_button:
                        section_name = tab_button.get_text(strip=True)

                content = self._extract_text_content(panel)

                sections.append(InteractiveSection(
                    section_type="tab",
                    section_name=section_name,
                    content=content,
                    selector=f"#{panel_id}" if panel_id else None
                ))

            except Exception as e:
                logger.debug(f"Error extracting tab: {e}")
                continue

        return sections

    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """
        Extract main content text from the page.

        Returns:
            Clean text content
        """
        # Try to find main content area
        main = soup.find("main")
        if not main:
            main = soup.find(["article", "div"], class_=lambda x: x and "content" in x.lower())
        if not main:
            main = soup

        return self._extract_text_content(main)

    def _extract_text_content(self, element: Tag) -> str:
        """
        Extract clean text from an element, preserving structure.

        Args:
            element: BeautifulSoup element

        Returns:
            Clean text with preserved structure
        """
        lines = []

        for child in element.descendants:
            if isinstance(child, NavigableString):
                text = str(child).strip()
                if text:
                    lines.append(text)
            elif isinstance(child, Tag):
                # Handle lists
                if child.name == "li":
                    text = child.get_text(strip=True)
                    if text:
                        # Check if it's in an ordered list
                        parent_ol = child.find_parent("ol")
                        if parent_ol:
                            # Get the index
                            siblings = [li for li in parent_ol.find_all("li", recursive=False)]
                            index = siblings.index(child) + 1 if child in siblings else 1
                            lines.append(f"{index}. {text}")
                        else:
                            lines.append(f"- {text}")

                # Handle headings
                elif child.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                    text = child.get_text(strip=True)
                    if text:
                        lines.append(f"\n{'#' * int(child.name[1])} {text}\n")

                # Handle paragraphs
                elif child.name == "p":
                    text = child.get_text(strip=True)
                    if text:
                        lines.append(f"\n{text}\n")

                # Handle tables (basic conversion)
                elif child.name == "table":
                    lines.append(self._extract_table(child))

        # Clean up and join
        text = "\n".join(lines)

        # Remove excessive newlines
        while "\n\n\n" in text:
            text = text.replace("\n\n\n", "\n\n")

        return text.strip()

    def _extract_table(self, table: Tag) -> str:
        """Convert table to text representation."""
        rows = []

        for tr in table.find_all("tr"):
            cells = []
            for cell in tr.find_all(["td", "th"]):
                cells.append(cell.get_text(strip=True))
            if cells:
                rows.append(" | ".join(cells))

        return "\n" + "\n".join(rows) + "\n" if rows else ""
