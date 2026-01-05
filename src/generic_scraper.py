"""
Generic web scraper orchestrator.
Manages the complete scraping workflow with smart link discovery and LLM extraction.
"""

import asyncio
import logging
from typing import List, Set, Dict, Any
from datetime import datetime
from pathlib import Path
from collections import deque

from src.models.generic import (
    JobConfig,
    GenericPageData,
    EnrichedPageData,
    CrawlResult,
    CrawlState
)
from src.crawler.browser import BrowserManager
from src.crawler.generic_crawler import GenericCrawler
from src.parser.generic_parser import GenericParser
from src.enrichment.llm_client import LLMClient
from src.enrichment.generic_enricher import GenericEnricher
from src.storage.file_manager import FileManager
from src.utils.delays import random_delay
from config.settings import Settings

logger = logging.getLogger(__name__)


class GenericScraper:
    """Orchestrates generic web scraping with LLM enrichment."""

    def __init__(self, settings: Settings):
        """
        Initialize generic scraper.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.file_manager = FileManager(settings)
        self.llm_client = LLMClient(settings)
        self.enricher = GenericEnricher(self.llm_client)

    async def scrape(self, job_config: JobConfig) -> CrawlResult:
        """
        Execute a complete scraping job.

        Args:
            job_config: Job configuration

        Returns:
            Final crawl result with synthesized data
        """
        start_time = datetime.now()
        logger.info(f"Starting scrape job: {job_config.job_name}")
        logger.info(f"Start URL: {job_config.start_url}")
        logger.info(f"Max depth: {job_config.crawl_config.depth}")
        logger.info(f"Max pages: {job_config.crawl_config.max_pages}")

        # Initialize crawl state
        crawl_state = CrawlState(
            job_name=job_config.job_name,
            start_url=str(job_config.start_url),
            queued_urls=[str(job_config.start_url)],
            visited_urls=[],
            failed_urls=[],
            current_depth=0,
            total_pages_scraped=0
        )

        # Stage 1: Crawl and parse all pages
        logger.info("=== Stage 1: Crawling Pages ===")
        scraped_pages = await self._crawl_all_pages(job_config, crawl_state)

        if not scraped_pages:
            logger.error("No pages were successfully scraped")
            return CrawlResult(
                job_name=job_config.job_name,
                start_url=str(job_config.start_url),
                crawl_metadata={
                    "total_pages": 0,
                    "duration_seconds": (datetime.now() - start_time).total_seconds(),
                    "error": "No pages scraped"
                },
                structured_data={}
            )

        # Save raw pages if requested
        if job_config.save_individual_pages:
            self._save_raw_pages(job_config.job_name, scraped_pages)

        # Stage 2: LLM enrichment per page
        logger.info("=== Stage 2: LLM Enrichment Per Page ===")
        enriched_pages = await self.enricher.enrich_multiple_pages(scraped_pages)

        # Save individual enriched pages if requested
        if job_config.save_individual_pages:
            self._save_enriched_pages(job_config.job_name, enriched_pages)

        # Stage 3: Final synthesis
        logger.info("=== Stage 3: Final Synthesis ===")
        crawl_metadata = {
            "total_pages": len(scraped_pages),
            "successful_enrichments": len(enriched_pages),
            "duration_seconds": (datetime.now() - start_time).total_seconds(),
            "visited_urls": crawl_state.visited_urls,
            "failed_urls": crawl_state.failed_urls,
        }

        if job_config.final_synthesis and len(enriched_pages) > 1:
            final_result = await self.enricher.synthesize_crawl_result(
                job_name=job_config.job_name,
                start_url=str(job_config.start_url),
                enriched_pages=enriched_pages,
                crawl_metadata=crawl_metadata
            )
        else:
            # No synthesis, just package the results
            main_page = next((p for p in enriched_pages if p.depth == 0), None)
            child_pages = [p for p in enriched_pages if p.depth > 0]

            final_result = CrawlResult(
                job_name=job_config.job_name,
                start_url=str(job_config.start_url),
                crawl_metadata=crawl_metadata,
                main_page=main_page,
                child_pages=child_pages,
                structured_data={},
                crawled_at=datetime.now()
            )

        # Save final result
        self._save_final_result(job_config.job_name, final_result)

        logger.info(f"Scrape job complete: {job_config.job_name}")
        logger.info(f"Total pages: {len(scraped_pages)}")
        logger.info(f"Duration: {crawl_metadata['duration_seconds']:.2f}s")

        return final_result

    async def _crawl_all_pages(
        self,
        job_config: JobConfig,
        crawl_state: CrawlState
    ) -> List[GenericPageData]:
        """
        Crawl all pages with breadth-first search.

        Args:
            job_config: Job configuration
            crawl_state: Crawl state tracker

        Returns:
            List of scraped pages
        """
        scraped_pages: List[GenericPageData] = []
        visited_urls: Set[str] = set()
        queue = deque([(str(job_config.start_url), 0)])  # (url, depth)

        async with BrowserManager(self.settings) as browser:
            page = await browser.context.new_page()
            crawler = GenericCrawler(page)

            while queue and len(scraped_pages) < job_config.crawl_config.max_pages:
                url, depth = queue.popleft()

                # Skip if already visited
                if url in visited_urls:
                    continue

                # Skip if depth exceeded
                if depth > job_config.crawl_config.depth:
                    continue

                visited_urls.add(url)
                logger.info(f"Crawling ({depth}/{job_config.crawl_config.depth}): {url}")

                try:
                    # Crawl the page
                    html, expanded_selectors = await crawler.crawl_page(
                        url,
                        expand_accordions=job_config.crawl_config.expand_accordions,
                        accordion_selectors=job_config.crawl_config.accordion_selectors
                    )

                    # Parse the page
                    parser = GenericParser(
                        url,
                        job_config.crawl_config.link_filter,
                        job_config.crawl_config.follow_all_links
                    )
                    page_data = parser.parse(
                        html,
                        parent_url=None if depth == 0 else str(job_config.start_url),
                        depth=depth,
                        content_area_selector=job_config.crawl_config.content_area_selector
                    )

                    scraped_pages.append(page_data)
                    crawl_state.visited_urls.append(url)
                    crawl_state.total_pages_scraped += 1

                    # Add discovered links to queue
                    for discovered_url in page_data.discovered_links:
                        if discovered_url not in visited_urls:
                            queue.append((discovered_url, depth + 1))
                            crawl_state.queued_urls.append(discovered_url)

                    logger.info(f"✓ Scraped: {page_data.title} ({len(page_data.discovered_links)} links found)")

                    # Delay between requests
                    await random_delay(
                        self.settings.MIN_DELAY_SECONDS,
                        self.settings.MAX_DELAY_SECONDS
                    )

                except Exception as e:
                    logger.error(f"Failed to crawl {url}: {e}")
                    crawl_state.failed_urls.append(url)
                    continue

        return scraped_pages

    def _save_raw_pages(self, job_name: str, pages: List[GenericPageData]):
        """Save raw scraped pages."""
        output_dir = Path(self.settings.DATA_DIR) / job_name / "raw_pages"
        output_dir.mkdir(parents=True, exist_ok=True)

        for i, page in enumerate(pages):
            filename = output_dir / f"page_{i:03d}_{self._url_to_filename(page.url)}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(page.model_dump_json(indent=2))

        logger.info(f"Saved {len(pages)} raw pages to {output_dir}")

    def _save_enriched_pages(self, job_name: str, pages: List[EnrichedPageData]):
        """Save individual enriched pages."""
        output_dir = Path(self.settings.DATA_DIR) / job_name / "enriched_pages"
        output_dir.mkdir(parents=True, exist_ok=True)

        for i, page in enumerate(pages):
            filename = output_dir / f"page_{i:03d}_{self._url_to_filename(page.url)}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(page.model_dump_json(indent=2))

        logger.info(f"Saved {len(pages)} enriched pages to {output_dir}")

    def _save_final_result(self, job_name: str, result: CrawlResult):
        """Save final crawl result."""
        output_dir = Path(self.settings.DATA_DIR) / job_name
        output_dir.mkdir(parents=True, exist_ok=True)

        filename = output_dir / "final_result.json"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(result.model_dump_json(indent=2))

        logger.info(f"Saved final result to {filename}")

    def _url_to_filename(self, url: str) -> str:
        """Convert URL to safe filename."""
        # Remove protocol
        filename = url.replace('https://', '').replace('http://', '')
        # Replace special characters
        filename = filename.replace('/', '_').replace('?', '_').replace('&', '_')
        # Limit length
        if len(filename) > 100:
            filename = filename[:100]
        return filename
