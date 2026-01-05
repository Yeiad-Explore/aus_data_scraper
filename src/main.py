"""Main CLI orchestrator for the Generic Web Scraper."""

import asyncio
from pathlib import Path

import click
import structlog

from config.logging_config import setup_logging
from config.settings import settings
from src.crawler.browser import BrowserManager
from src.crawler.detail_crawler import DetailCrawler
from src.crawler.listing_crawler import ListingCrawler
from src.parser.detail_parser import DetailParser
from src.parser.listing_parser import ListingParser
from src.storage.file_manager import FileManager
from src.storage.state_manager import StateManager
from src.utils.delays import random_delay
from src.utils.validation import validate_all_files

logger = structlog.get_logger()


@click.group()
@click.option("--verbose", is_flag=True, help="Enable verbose logging")
def cli(verbose: bool):
    """Generic Web Scraper.

    A deterministic web scraper for extracting structured content from websites.
    """
    log_level = "DEBUG" if verbose else "INFO"
    log_file = settings.LOGS_DIR / "scraper.log"
    setup_logging(log_file=log_file, console_level=log_level)


@cli.command()
@click.option("--skip-enrichment", is_flag=True, help="Skip LLM enrichment phase")
@click.option("--fresh", is_flag=True, help="Ignore state and start fresh")
@click.option("--limit", type=int, default=None, help="Limit number of pages to scrape (for testing)")
@click.option("--link-pattern", type=str, default=None, help="Regex pattern to filter links (e.g., '/visas/')")
def scrape(skip_enrichment: bool, fresh: bool, limit: int | None, link_pattern: str | None):
    """Run the full scraping pipeline: crawl -> parse -> enrich."""
    asyncio.run(_scrape(skip_enrichment, fresh, limit, link_pattern))


async def _scrape(skip_enrichment: bool, fresh: bool, limit: int | None, link_pattern: str | None):
    """Execute the scraping pipeline.

    Args:
        skip_enrichment: Skip LLM enrichment phase
        fresh: Reset state and start from scratch
        limit: Maximum number of pages to scrape (None for all)
        link_pattern: Regex pattern to filter links (None for all links)
    """
    logger.info(
        "scrape_started",
        skip_enrichment=skip_enrichment,
        fresh=fresh,
        limit=limit,
    )

    # Initialize components
    file_manager = FileManager(settings)
    state_manager = StateManager(settings.STATE_DIR)

    if fresh:
        state_manager.reset()
        logger.info("state_reset_fresh_start")

    # Phase 1: Crawl listing page
    logger.info("phase_1_crawl_listing_page")

    async with BrowserManager(settings) as browser_manager:
        page = await browser_manager.new_page()

        # Crawl listing page
        listing_crawler = ListingCrawler(settings)
        listing_html = await listing_crawler.crawl(page)
        file_manager.save_raw_html(settings.ENTRY_URL, listing_html)

        # Parse listing page
        listing_parser = ListingParser(settings.BASE_URL, link_pattern=link_pattern)
        content_listings = listing_parser.parse(listing_html)

        logger.info("content_listings_found", count=len(content_listings))

        # Apply limit if specified
        if limit:
            content_listings = content_listings[:limit]
            logger.info("limit_applied", scraping_count=len(content_listings))

        # Phase 2: Crawl and parse each detail page
        logger.info("phase_2_crawl_details", total=len(content_listings))

        detail_crawler = DetailCrawler(settings)
        detail_parser = DetailParser()

        for i, listing in enumerate(content_listings, 1):
            # Check if already completed
            if state_manager.is_completed(listing.url):
                logger.info(
                    "skipping_completed",
                    url=listing.url,
                    progress=f"{i}/{len(content_listings)}",
                )
                continue

            try:
                # Apply anti-blocking delay (except for first request)
                if i > 1:
                    await random_delay(
                        settings.MIN_DELAY_SECONDS,
                        settings.MAX_DELAY_SECONDS,
                    )

                # Crawl detail page
                detail_html = await detail_crawler.crawl(page, listing.url)
                file_manager.save_raw_html(listing.url, detail_html)

                # Parse detail page
                content_data = detail_parser.parse(
                    detail_html,
                    listing.url,
                    listing.category,
                )
                file_manager.save_parsed_json(listing.url, content_data)

                # Mark as completed
                state_manager.mark_completed(listing.url)

                logger.info(
                    "content_processed",
                    progress=f"{i}/{len(content_listings)}",
                    title=listing.title,
                    url=listing.url,
                )

            except Exception as e:
                logger.error(
                    "content_processing_failed",
                    url=listing.url,
                    title=listing.title,
                    error=str(e),
                    progress=f"{i}/{len(content_listings)}",
                )
                # Continue to next page (fail loudly but don't abort)
                continue

        await page.close()

    # Phase 3: Optional enrichment
    if not skip_enrichment and settings.LLM_API_KEY:
        logger.info("phase_3_llm_enrichment")
        await _enrich_all(file_manager)
    elif not skip_enrichment and not settings.LLM_API_KEY:
        logger.warning("enrichment_skipped_no_api_key")

    # Summary
    stats = state_manager.get_stats()
    logger.info(
        "scrape_completed",
        completed_count=stats["completed_count"],
        total_pages=len(content_listings),
    )

    click.echo(f"\n[OK] Scraping completed!")
    click.echo(f"   Pages processed: {stats['completed_count']}/{len(content_listings)}")
    click.echo(f"   Raw HTML: {settings.RAW_DIR}")
    click.echo(f"   Parsed JSON: {settings.PARSED_DIR}")
    click.echo(f"   Logs: {settings.LOGS_DIR}")


async def _enrich_all(file_manager: FileManager):
    """Enrich all parsed JSONs with LLM classification.

    Args:
        file_manager: FileManager instance
    """
    try:
        from src.enrichment.enricher import ContentEnricher
        from src.enrichment.llm_client import LLMClient

        llm_client = LLMClient(settings)
        enricher = ContentEnricher(llm_client)

        parsed_files = file_manager.get_all_parsed_files()
        logger.info("enriching_content", count=len(parsed_files))

        for i, file_path in enumerate(parsed_files, 1):
            try:
                # Load parsed content
                content_data = file_manager.load_parsed_json(file_path.stem)

                # Enrich with LLM
                enriched_data = await enricher.enrich(content_data)

                # Save enriched data
                file_manager.save_enriched_json(content_data.source_url, enriched_data)

                logger.info(
                    "content_enriched",
                    progress=f"{i}/{len(parsed_files)}",
                    title=content_data.title,
                )

            except Exception as e:
                logger.error(
                    "enrichment_failed",
                    file=file_path.name,
                    error=str(e),
                )
                continue

        logger.info("enrichment_completed", total=len(parsed_files))

    except ImportError as e:
        logger.error("enrichment_import_failed", error=str(e))
        click.echo(f"[ERROR] Enrichment failed: {e}")


@cli.command()
@click.argument("url")
@click.option("--name", "-n", required=True, help="Job name for this scrape")
@click.option("--depth", "-d", type=int, default=1, help="Maximum crawl depth (default: 1)")
@click.option("--max-pages", "-m", type=int, default=50, help="Maximum pages to scrape (default: 50)")
@click.option("--filter", "-f", type=click.Choice(["same_path", "same_domain", "all"]), default="same_path", help="Link filter strategy")
@click.option("--follow-all-links", is_flag=True, help="Follow ALL links on page, not just structural ones (tiles/cards)")
@click.option("--no-synthesis", is_flag=True, help="Skip final LLM synthesis")
@click.option("--no-individual", is_flag=True, help="Don't save individual page extractions")
def scrape_generic(url: str, name: str, depth: int, max_pages: int, filter: str, follow_all_links: bool, no_synthesis: bool, no_individual: bool):
    """Scrape any website with intelligent content extraction.

    This command scrapes a website starting from URL, intelligently discovers
    related pages, and uses LLM to extract structured data.

    Example:
      python -m src.main scrape-generic \\
        "https://immi.homeaffairs.gov.au/visas/getting-a-visa/visa-listing" \\
        --name visa-full --depth 1 --max-pages 150 --filter same_domain --follow-all-links
    """
    asyncio.run(_scrape_generic(url, name, depth, max_pages, filter, follow_all_links, no_synthesis, no_individual))


async def _scrape_generic(
    url: str,
    name: str,
    depth: int,
    max_pages: int,
    filter: str,
    follow_all_links: bool,
    no_synthesis: bool,
    no_individual: bool
):
    """Execute generic scraping.

    Args:
        url: Starting URL
        name: Job name
        depth: Maximum crawl depth
        max_pages: Maximum pages to scrape
        filter: Link filter strategy
        follow_all_links: Follow all links, not just structural ones
        no_synthesis: Skip final synthesis
        no_individual: Don't save individual pages
    """
    from src.models.generic import JobConfig, CrawlConfig
    from src.generic_scraper import GenericScraper

    logger.info(
        "generic_scrape_started",
        url=url,
        name=name,
        depth=depth,
        max_pages=max_pages,
        filter=filter,
        follow_all_links=follow_all_links
    )

    # Create job configuration
    crawl_config = CrawlConfig(
        depth=depth,
        max_pages=max_pages,
        link_filter=filter,
        follow_all_links=follow_all_links
    )

    job_config = JobConfig(
        job_name=name,
        start_url=url,
        crawl_config=crawl_config,
        save_individual_pages=not no_individual,
        final_synthesis=not no_synthesis
    )

    # Run the scraper
    try:
        scraper = GenericScraper(settings)
        result = await scraper.scrape(job_config)

        # Display results
        click.echo(f"\n[OK] Scraping completed!")
        click.echo(f"   Job name: {name}")
        click.echo(f"   Pages scraped: {result.crawl_metadata.get('total_pages', 0)}")
        click.echo(f"   Duration: {result.crawl_metadata.get('duration_seconds', 0):.2f}s")
        click.echo(f"   Output: {settings.DATA_DIR / name}")

        if result.crawl_metadata.get('failed_urls'):
            click.echo(f"   Failed URLs: {len(result.crawl_metadata['failed_urls'])}")

    except Exception as e:
        logger.error("generic_scrape_failed", error=str(e))
        click.echo(f"\n[ERROR] Scraping failed: {e}")
        raise


@cli.command()
@click.option(
    "--type",
    "file_type",
    type=click.Choice(["parsed", "enriched"]),
    default="parsed",
    help="Type of files to validate",
)
def validate(file_type: str):
    """Validate all scraped JSON files."""
    logger.info("validation_started", file_type=file_type)

    if file_type == "parsed":
        directory = settings.PARSED_DIR
    else:
        directory = settings.ENRICHED_DIR

    stats = validate_all_files(directory)

    logger.info("validation_completed", stats=stats)

    click.echo(f"\nValidation Results ({file_type}):")
    click.echo(f"   Total files: {stats['total']}")
    click.echo(f"   Valid: {stats['valid']}")
    click.echo(f"   Invalid: {stats['invalid']}")

    if stats["invalid"] > 0:
        click.echo(f"\n[ERROR] Invalid files:")
        for error_file in stats["errors"]:
            click.echo(f"   - {error_file}")
    else:
        click.echo(f"\n[OK] All files are valid!")


@cli.command()
def stats():
    """Show scraping statistics."""
    state_manager = StateManager(settings.STATE_DIR)
    stats_data = state_manager.get_stats()

    click.echo(f"\nScraping Statistics:")
    click.echo(f"   Completed pages: {stats_data['completed_count']}")
    click.echo(f"   State file: {stats_data['state_file']}")
    click.echo(f"   State exists: {stats_data['state_file_exists']}")

    # Count files
    if settings.RAW_DIR.exists():
        raw_count = len(list(settings.RAW_DIR.glob("*.html")))
        click.echo(f"   Raw HTML files: {raw_count}")

    if settings.PARSED_DIR.exists():
        parsed_count = len(list(settings.PARSED_DIR.glob("*.json")))
        click.echo(f"   Parsed JSON files: {parsed_count}")

    if settings.ENRICHED_DIR.exists():
        enriched_count = len(list(settings.ENRICHED_DIR.glob("*.json")))
        click.echo(f"   Enriched JSON files: {enriched_count}")


@cli.command()
@click.confirmation_option(prompt="Are you sure you want to reset all state?")
def reset():
    """Reset scraping state (keeps data files)."""
    state_manager = StateManager(settings.STATE_DIR)
    state_manager.reset()

    click.echo("[OK] State reset successfully!")
    click.echo("   Note: Data files are preserved. Run 'scrape --fresh' to re-scrape.")


@cli.command()
@click.option("--host", default="0.0.0.0", help="Host to bind the API server to")
@click.option("--port", type=int, default=8000, help="Port to run the API server on")
@click.option("--reload", is_flag=True, help="Enable auto-reload for development")
def api(host: str, port: int, reload: bool):
    """Start the REST API server for scraping.

    The API accepts POST requests with JSON body containing scraping parameters.

    Example POST request:
    {
        "url": "https://example.com",
        "name": "my_scrape",
        "depth": 1,
        "max_pages": 10,
        "filter": "same_path"
    }
    """
    import uvicorn

    click.echo(f"\n[OK] Starting API server...")
    click.echo(f"   Host: {host}")
    click.echo(f"   Port: {port}")
    click.echo(f"   API docs: http://{host if host != '0.0.0.0' else 'localhost'}:{port}/docs")
    click.echo(f"   Reload: {reload}\n")

    try:
        uvicorn.run(
            "src.api:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )
    except KeyboardInterrupt:
        click.echo("\n\n[OK] API server stopped.")


@cli.command()
@click.option("--port", type=int, default=8000, help="Port to run the server on")
def serve(port: int):
    """Start the web server to view scraped data."""
    import subprocess
    import sys
    from pathlib import Path

    web_dir = Path(__file__).parent.parent / "web"
    server_script = web_dir / "server.py"

    if not server_script.exists():
        click.echo("[ERROR] Web server not found. Check installation.")
        return

    click.echo(f"\nStarting web server on port {port}...")
    click.echo(f"Open http://localhost:{port} in your browser\n")

    try:
        subprocess.run([sys.executable, str(server_script), "--port", str(port)])
    except KeyboardInterrupt:
        click.echo("\n\n[OK] Server stopped.")


if __name__ == "__main__":
    cli()
