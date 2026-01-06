"""
Simple script to run the generic web scraper.

Usage:
    python run.py <url> [options]

Example:
    python run.py https://example.com --name my-scrape --depth 2 --max-pages 10
"""

import asyncio
import argparse
from generic_scraper import GenericScraper
from models import JobConfig, CrawlConfig
from settings import Settings


async def main():
    parser = argparse.ArgumentParser(description="Generic Web Scraper")
    parser.add_argument("url", help="Starting URL to scrape")
    parser.add_argument("--name", default="scrape-job", help="Job name for output folder")
    parser.add_argument("--depth", type=int, default=1, help="Maximum crawl depth (0-5)")
    parser.add_argument("--max-pages", type=int, default=50, help="Maximum pages to scrape")
    parser.add_argument(
        "--filter",
        choices=["same_path", "same_domain", "all"],
        default="same_path",
        help="Link filter strategy"
    )
    parser.add_argument("--follow-all", action="store_true", help="Follow all links")
    parser.add_argument("--no-enrich", action="store_true", help="Skip LLM enrichment")
    parser.add_argument("--no-synthesis", action="store_true", help="Skip final synthesis")

    args = parser.parse_args()

    # Build configuration
    crawl_config = CrawlConfig(
        depth=args.depth,
        max_pages=args.max_pages,
        link_filter=args.filter,
        follow_all_links=args.follow_all,
    )

    job_config = JobConfig(
        job_name=args.name,
        start_url=args.url,
        crawl_config=crawl_config,
        save_individual_pages=True,
        final_synthesis=not args.no_synthesis,
    )

    # Initialize and run scraper
    settings = Settings()
    scraper = GenericScraper(settings)

    print(f"Starting scrape: {args.url}")
    print(f"Job name: {args.name}")
    print(f"Depth: {args.depth}, Max pages: {args.max_pages}")

    result = await scraper.scrape(job_config)

    print(f"\nScrape complete!")
    print(f"Pages scraped: {result.crawl_metadata.get('total_pages', 0)}")
    print(f"Duration: {result.crawl_metadata.get('duration_seconds', 0):.2f}s")
    print(f"Output: {settings.DATA_DIR / args.name}")


if __name__ == "__main__":
    asyncio.run(main())
