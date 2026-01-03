"""Parser for visa detail page DOM."""

import re
from typing import List

import structlog
from bs4 import BeautifulSoup, NavigableString

from src.models.visa import VisaData, VisaSection

logger = structlog.get_logger()


class DetailParser:
    """Parses visa detail page DOM to extract structured content.

    This parser removes navigation/junk elements and extracts the main
    visa information preserving section structure.
    """

    # Elements to remove from the DOM
    IGNORE_SELECTORS = [
        "nav",
        "header",
        "footer",
        "aside",
        ".breadcrumb",
        ".breadcrumbs",
        ".navigation",
        ".nav",
        ".cookie-banner",
        ".cookie-consent",
        '[role="navigation"]',
        '[aria-label="breadcrumb"]',
        ".back-to-top",
        ".skip-link",
        "#skip-link",
    ]

    def parse(self, html: str, url: str, category: str = "") -> VisaData:
        """Extract structured content from visa detail page.

        Args:
            html: Raw HTML content
            url: Source URL
            category: Visa category (from listing page)

        Returns:
            VisaData object with extracted information
        """
        soup = BeautifulSoup(html, "lxml")

        # Remove navigation and junk elements
        self._remove_junk(soup)

        # Extract key fields
        visa_name = self._extract_visa_name(soup)
        subclass = self._extract_subclass(soup, visa_name)
        summary = self._extract_summary(soup)
        sections = self._extract_sections(soup)

        visa = VisaData(
            visa_name=visa_name,
            subclass=subclass,
            category=category,
            summary=summary,
            sections=sections,
            source_url=url,
        )

        total_text = sum(len(s.content) for s in sections)
        logger.info(
            "detail_parsed",
            visa_name=visa_name,
            section_count=len(sections),
            total_text_length=total_text,
        )

        return visa

    def _remove_junk(self, soup: BeautifulSoup) -> None:
        """Remove navigation, footer, and other junk elements.

        Args:
            soup: BeautifulSoup object (modified in place)
        """
        for selector in self.IGNORE_SELECTORS:
            for element in soup.select(selector):
                element.decompose()

    def _extract_visa_name(self, soup: BeautifulSoup) -> str:
        """Extract visa name from h1 heading.

        Args:
            soup: BeautifulSoup object

        Returns:
            Visa name or empty string
        """
        h1 = soup.find("h1")
        if h1:
            return self._clean_text(h1.get_text())
        return ""

    def _extract_subclass(self, soup: BeautifulSoup, visa_name: str) -> str:
        """Extract visa subclass number.

        Looks for patterns like "Subclass 482" or "(482)" in the page.

        Args:
            soup: BeautifulSoup object
            visa_name: Visa name (to search within)

        Returns:
            Subclass number or empty string
        """
        # Check visa name first
        match = re.search(r"\b(\d{3})\b", visa_name)
        if match:
            return match.group(1)

        # Look in common locations
        search_elements = [
            soup.find("h1"),
            soup.find(class_=re.compile(r"subclass", re.I)),
            soup.find(text=re.compile(r"subclass\s*\d{3}", re.I)),
        ]

        for element in search_elements:
            if element:
                text = element.get_text() if hasattr(element, "get_text") else str(element)
                match = re.search(r"\b(\d{3})\b", text)
                if match:
                    return match.group(1)

        return ""

    def _extract_summary(self, soup: BeautifulSoup) -> str:
        """Extract first significant paragraph as summary.

        Args:
            soup: BeautifulSoup object

        Returns:
            Summary text or empty string
        """
        # Find main content area
        main_content = soup.find("main") or soup.find("article") or soup.body

        if not main_content:
            return ""

        # Find first paragraph after h1
        h1 = main_content.find("h1")
        if h1:
            # Look for next paragraph
            next_p = h1.find_next("p")
            if next_p:
                text = self._clean_text(next_p.get_text())
                # Only use if it's substantial
                if len(text) > 20:
                    return text

        # Fallback: find first substantial paragraph
        for p in main_content.find_all("p", limit=5):
            text = self._clean_text(p.get_text())
            if len(text) > 20:
                return text

        return ""

    def _extract_sections(self, soup: BeautifulSoup) -> List[VisaSection]:
        """Extract all content sections with their headings.

        Args:
            soup: BeautifulSoup object

        Returns:
            List of VisaSection objects
        """
        sections = []

        # Find main content area
        main_content = soup.find("main") or soup.find("article") or soup.body

        if not main_content:
            return sections

        current_section_title = None
        current_section_content = []

        # Iterate through all top-level elements
        for element in main_content.children:
            # Skip navigable strings (text nodes)
            if isinstance(element, NavigableString):
                continue

            # Check if this is a heading (new section)
            if element.name in ["h2", "h3"]:
                # Save previous section if it exists
                if current_section_title:
                    content = self._join_content(current_section_content)
                    if content:  # Only add if content is not empty
                        sections.append(
                            VisaSection(title=current_section_title, content=content)
                        )

                # Start new section
                current_section_title = self._clean_text(element.get_text())
                current_section_content = []

            # Collect content for current section
            elif current_section_title and element.name in ["p", "ul", "ol", "div", "table"]:
                text = self._extract_text_with_structure(element)
                if text:
                    current_section_content.append(text)

        # Save last section
        if current_section_title:
            content = self._join_content(current_section_content)
            if content:
                sections.append(VisaSection(title=current_section_title, content=content))

        # If no sections were found, try a fallback approach
        if not sections:
            sections = self._extract_sections_fallback(main_content)

        return sections

    def _extract_sections_fallback(self, main_content) -> List[VisaSection]:
        """Fallback section extraction if primary method finds nothing.

        Args:
            main_content: Main content element

        Returns:
            List of VisaSection objects
        """
        sections = []

        # Find all headings
        headings = main_content.find_all(["h2", "h3", "h4"])

        for heading in headings:
            title = self._clean_text(heading.get_text())
            if not title:
                continue

            # Collect content until next heading
            content_parts = []
            for sibling in heading.find_next_siblings():
                if sibling.name in ["h2", "h3", "h4"]:
                    break

                if sibling.name in ["p", "ul", "ol", "div", "table"]:
                    text = self._extract_text_with_structure(sibling)
                    if text:
                        content_parts.append(text)

            content = self._join_content(content_parts)
            if content:
                sections.append(VisaSection(title=title, content=content))

        return sections

    def _extract_text_with_structure(self, element) -> str:
        """Extract text from element while preserving structure (bullets, etc.).

        Args:
            element: BeautifulSoup element

        Returns:
            Formatted text
        """
        if element.name == "ul":
            items = []
            for li in element.find_all("li", recursive=False):
                text = self._clean_text(li.get_text())
                if text:
                    items.append(f"- {text}")
            return "\n".join(items)

        elif element.name == "ol":
            items = []
            for i, li in enumerate(element.find_all("li", recursive=False), 1):
                text = self._clean_text(li.get_text())
                if text:
                    items.append(f"{i}. {text}")
            return "\n".join(items)

        elif element.name == "table":
            # Simple table text extraction
            rows = []
            for tr in element.find_all("tr"):
                cells = [self._clean_text(td.get_text()) for td in tr.find_all(["td", "th"])]
                if any(cells):
                    rows.append(" | ".join(cells))
            return "\n".join(rows)

        else:
            # Regular text extraction
            return self._clean_text(element.get_text())

    def _clean_text(self, text: str) -> str:
        """Clean text by removing extra whitespace and junk.

        Args:
            text: Raw text

        Returns:
            Cleaned text
        """
        if not text:
            return ""

        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text)

        # Remove common junk phrases
        junk_patterns = [
            r"back to top",
            r"skip to content",
            r"skip to main content",
            r"print this page",
            r"share this page",
        ]

        for pattern in junk_patterns:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)

        return text.strip()

    def _join_content(self, content_list: List[str]) -> str:
        """Join content blocks with double newlines.

        Args:
            content_list: List of content strings

        Returns:
            Joined content
        """
        # Filter out empty strings
        content_list = [c for c in content_list if c.strip()]
        return "\n\n".join(content_list)
