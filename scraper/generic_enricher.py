"""
Generic enricher for 3-stage LLM processing.
Extracts structured data from pages and synthesizes them into cohesive output.
"""

import asyncio
import logging
from typing import List, Dict, Any
from datetime import datetime

from models import GenericPageData, EnrichedPageData, CrawlResult
from llm_client import LLMClient

logger = logging.getLogger(__name__)


class GenericEnricher:
    """Enriches scraped pages with LLM-extracted structured data."""

    def __init__(self, llm_client: LLMClient):
        """
        Initialize enricher.

        Args:
            llm_client: LLM client for extraction
        """
        self.llm = llm_client

    async def enrich_page(self, page_data: GenericPageData) -> EnrichedPageData:
        """
        Enrich a single page with LLM extraction.

        Args:
            page_data: Raw scraped page data

        Returns:
            Enriched page data with structured information
        """
        logger.info(f"Enriching page: {page_data.title}")

        # Use raw_text if available (preferred), otherwise fall back to combining content
        if page_data.raw_text:
            full_content = page_data.raw_text
        else:
            full_content = self._combine_content(page_data)

        # Extract structured data using LLM from plain text
        extraction_result = await self.llm.extract_structured_data(
            page_title=page_data.title,
            content=full_content
        )

        # Create enriched page data
        enriched = EnrichedPageData(
            url=page_data.url,
            title=page_data.title,
            content_type=extraction_result.get("content_type"),
            summary=extraction_result.get("summary"),
            structured_data=extraction_result.get("structured_data", {}),
            parent_url=page_data.parent_url,
            depth=page_data.depth
        )

        return enriched

    async def enrich_multiple_pages(
        self,
        pages: List[GenericPageData],
        batch_size: int = 5
    ) -> List[EnrichedPageData]:
        """
        Enrich multiple pages in batches.

        Args:
            pages: List of page data to enrich
            batch_size: Number of pages to process concurrently

        Returns:
            List of enriched page data
        """
        logger.info(f"Enriching {len(pages)} pages (batch size: {batch_size})")

        enriched_pages = []

        # Process in batches to avoid overwhelming the API
        for i in range(0, len(pages), batch_size):
            batch = pages[i:i + batch_size]
            logger.info(f"Processing batch {i // batch_size + 1}/{(len(pages) + batch_size - 1) // batch_size}")

            # Process batch concurrently
            tasks = [self.enrich_page(page) for page in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Filter out exceptions
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Failed to enrich page: {result}")
                else:
                    enriched_pages.append(result)

            # Small delay between batches
            if i + batch_size < len(pages):
                await asyncio.sleep(1)

        logger.info(f"Successfully enriched {len(enriched_pages)}/{len(pages)} pages")
        return enriched_pages

    async def synthesize_crawl_result(
        self,
        job_name: str,
        start_url: str,
        enriched_pages: List[EnrichedPageData],
        crawl_metadata: Dict[str, Any]
    ) -> CrawlResult:
        """
        Synthesize all enriched pages into final result.

        Args:
            job_name: Name of the scraping job
            start_url: Starting URL
            enriched_pages: List of enriched pages
            crawl_metadata: Metadata about the crawl

        Returns:
            Final crawl result with synthesized data
        """
        logger.info(f"Synthesizing {len(enriched_pages)} pages into final result")

        if not enriched_pages:
            logger.warning("No enriched pages to synthesize")
            return CrawlResult(
                job_name=job_name,
                start_url=start_url,
                crawl_metadata=crawl_metadata,
                structured_data={}
            )

        # Find main page (depth 0)
        main_page = next((p for p in enriched_pages if p.depth == 0), None)
        child_pages = [p for p in enriched_pages if p.depth > 0]

        # Prepare data for synthesis
        pages_data = []
        for page in enriched_pages:
            pages_data.append({
                "url": page.url,
                "title": page.title,
                "content_type": page.content_type,
                "summary": page.summary,
                "structured_data": page.structured_data
            })

        # Synthesize with LLM
        synthesized_data = await self.llm.synthesize_pages(pages_data)

        result = CrawlResult(
            job_name=job_name,
            start_url=start_url,
            crawl_metadata=crawl_metadata,
            main_page=main_page,
            child_pages=child_pages,
            structured_data=synthesized_data,
            crawled_at=datetime.now()
        )

        logger.info("Synthesis complete")
        return result

    def _combine_content(self, page_data: GenericPageData) -> str:
        """
        Combine all content from a page into a single string.

        Args:
            page_data: Page data

        Returns:
            Combined content string
        """
        parts = []

        # Add main content
        if page_data.main_content:
            parts.append("=== Main Content ===")
            parts.append(page_data.main_content)

        # Add interactive sections
        if page_data.interactive_sections:
            parts.append("\n=== Interactive Sections ===")
            for section in page_data.interactive_sections:
                parts.append(f"\n[{section.section_type.upper()}] {section.section_name}")
                parts.append(section.content)

        # Add referenced links (just mention them)
        if page_data.referenced_links:
            parts.append("\n=== Referenced Links ===")
            for link in page_data.referenced_links[:10]:  # Limit to first 10
                parts.append(f"- {link.text}: {link.url}")

        return "\n".join(parts)
