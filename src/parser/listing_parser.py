"""Parser for visa listing page DOM."""

import json
import re
from html import unescape
from typing import List

import structlog
from bs4 import BeautifulSoup

from src.models.listing import VisaListing
from src.utils.url_utils import normalize_url

logger = structlog.get_logger()


class ListingParser:
    """Parses visa listing page DOM to extract visa cards.

    This parser extracts visa links from the hidden JSON field in the page,
    which contains all visa categories and their links in a structured format.
    """

    def __init__(self, base_url: str):
        """Initialize listing parser.

        Args:
            base_url: Base URL for normalizing relative links
        """
        self.base_url = base_url

    def parse(self, html: str) -> List[VisaListing]:
        """Extract all visa cards from listing page HTML.

        First tries to extract from the hidden JSON field (most reliable),
        then falls back to DOM parsing if JSON is not found.

        Args:
            html: Raw HTML content from listing page

        Returns:
            List of VisaListing objects
        """
        soup = BeautifulSoup(html, "lxml")
        visas = []

        # Try to extract from hidden JSON field first (most reliable)
        json_visas = self._parse_from_json_field(soup)
        if json_visas:
            visas.extend(json_visas)
            logger.info("visas_extracted_from_json", count=len(json_visas))

        # Fallback: Find all links that look like visa links
        # This ensures we don't miss any visas if JSON parsing fails
        dom_visas = self._parse_from_dom(soup)
        
        # Merge results, avoiding duplicates
        existing_urls = {v.visa_url for v in visas}
        for visa in dom_visas:
            if visa.visa_url not in existing_urls:
                visas.append(visa)
                existing_urls.add(visa.visa_url)

        logger.info("listing_parsed", visa_count=len(visas), json_count=len(json_visas), dom_count=len(dom_visas))

        return visas

    def _parse_from_json_field(self, soup: BeautifulSoup) -> List[VisaListing]:
        """Extract visas from the hidden JSON input field.

        The page contains a hidden input with id containing 'PageSchemaHiddenField'
        that has a JSON value with all visa categories and links.

        Args:
            soup: BeautifulSoup object of the page

        Returns:
            List of VisaListing objects extracted from JSON
        """
        visas = []

        try:
            # Find the hidden input field containing the JSON data
            # The ID pattern is: ctl00_PlaceHolderMain_PageSchemaHiddenField_Input
            hidden_input = soup.find("input", {"id": re.compile(r".*PageSchemaHiddenField.*")})
            
            if not hidden_input or "value" not in hidden_input.attrs:
                logger.debug("json_field_not_found")
                return visas

            # Parse the JSON value
            json_str = hidden_input["value"]
            # Unescape HTML entities in the JSON string
            json_str = unescape(json_str)
            
            data = json.loads(json_str)
            
            # Extract visas from each category
            if "content" in data and isinstance(data["content"], list):
                for category_item in data["content"]:
                    category_name = category_item.get("text", "").strip()
                    block_html = category_item.get("block", "")
                    
                    if not block_html:
                        continue
                    
                    # Parse the HTML block to extract links
                    block_soup = BeautifulSoup(block_html, "lxml")
                    links = block_soup.find_all("a", href=True)
                    
                    for link in links:
                        href = link.get("href", "").strip()
                        visa_name = link.get_text(strip=True)
                        
                        # Skip if not a valid visa link
                        if not href or not visa_name:
                            continue
                        
                        # Skip the listing page itself
                        if href == "/visas/getting-a-visa/visa-listing" or href.startswith("/visas/getting-a-visa/visa-listing?"):
                            continue
                        
                        # Remove anchors and query parameters for normalization
                        # (we want to scrape the same page even if linked with different anchors)
                        clean_href = href.split("#")[0].split("?")[0]
                        
                        # Remove trailing slash for consistency
                        clean_href = clean_href.rstrip("/")
                        
                        # Normalize URL
                        visa_url = normalize_url(clean_href, self.base_url)
                        
                        # Extract subclass from visa name
                        subclass = self._extract_subclass_from_text(visa_name)
                        
                        # Create VisaListing
                        visa = VisaListing(
                            category=category_name,
                            visa_name=visa_name,
                            subclass=subclass,
                            visa_url=visa_url,
                        )
                        
                        visas.append(visa)

        except json.JSONDecodeError as e:
            logger.warning("json_parse_failed", error=str(e))
        except Exception as e:
            logger.warning("json_extraction_failed", error=str(e))

        return visas

    def _parse_from_dom(self, soup: BeautifulSoup) -> List[VisaListing]:
        """Fallback: Extract visas by parsing DOM links.

        Args:
            soup: BeautifulSoup object of the page

        Returns:
            List of VisaListing objects extracted from DOM
        """
        visas = []
        links = soup.find_all("a", href=True)

        for link in links:
            href = link.get("href", "").strip()
            
            # Skip the listing page itself
            if not href or href == "/visas/getting-a-visa/visa-listing" or href.startswith("/visas/getting-a-visa/visa-listing?"):
                continue

            # Check if this looks like a visa detail page
            if "/visas/" in href:
                visa = self._parse_visa_link(link, soup)
                if visa and visa.visa_url not in [v.visa_url for v in visas]:
                    visas.append(visa)

        return visas

    def _parse_visa_link(self, link, soup: BeautifulSoup) -> VisaListing | None:
        """Parse a visa link element to extract metadata.

        Args:
            link: BeautifulSoup link element
            soup: Full page soup for context

        Returns:
            VisaListing object or None if parsing fails
        """
        try:
            href = link.get("href", "").strip()
            
            # Remove anchors and query parameters for normalization
            clean_href = href.split("#")[0].split("?")[0]
            # Remove trailing slash for consistency
            clean_href = clean_href.rstrip("/")
            
            # Normalize URL
            visa_url = normalize_url(clean_href, self.base_url)

            # Get visa name from link text
            visa_name = link.get_text(strip=True)

            # Skip if no text
            if not visa_name:
                return None

            # Try to find category by looking at parent elements
            category = self._extract_category(link)

            # Try to extract subclass from link text or surrounding context
            subclass = self._extract_subclass_from_text(visa_name)
            
            # Also check surrounding context for subclass
            if not subclass:
                parent = link.find_parent(["div", "li", "article"])
                if parent:
                    subclass = self._extract_subclass_from_text(parent.get_text())

            return VisaListing(
                category=category,
                visa_name=visa_name,
                subclass=subclass,
                visa_url=visa_url,
            )

        except Exception as e:
            logger.debug("visa_link_parsing_failed", error=str(e))
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
                # Skip if it's just "Visa" or too generic
                if text and text.lower() not in ["visa", "visas"]:
                    return text

        return ""

    def _extract_subclass_from_text(self, text: str) -> str:
        """Extract visa subclass number from text.

        Looks for patterns like "Subclass 482", "(482)", "482 visa", etc.

        Args:
            text: Text to search for subclass patterns

        Returns:
            Subclass number or empty string
        """
        if not text:
            return ""

        # Common subclass patterns - order matters (more specific first)
        patterns = [
            r"subclass\s*(\d{3})\s+(\d{3})",  # Subclass 309 100 (multiple subclasses - take first)
            r"subclass\s*(\d{3})\s*visa",  # Subclass 482 visa
            r"subclass\s*(\d{3})",  # Subclass 482
            r"\(subclass\s*(\d{3})\)",  # (subclass 482) or (subclass 010)
            r"\((\d{3})\)",  # (482)
            r"(\d{3})\s*visa",  # 482 visa
            r"visa\s*(\d{3})",  # Visa 482
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # If pattern has multiple groups (like subclass 309 100), return first
                return match.group(1)

        return ""
