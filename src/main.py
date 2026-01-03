"""Main CLI orchestrator for the Australian Home Affairs Visa Scraper."""

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
    """Australian Home Affairs Visa Scraper.

    A deterministic web scraper for Australian visa information.
    """
    log_level = "DEBUG" if verbose else "INFO"
    log_file = settings.LOGS_DIR / "scraper.log"
    setup_logging(log_file=log_file, console_level=log_level)


@cli.command()
@click.option("--skip-enrichment", is_flag=True, help="Skip LLM enrichment phase")
@click.option("--fresh", is_flag=True, help="Ignore state and start fresh")
@click.option("--limit", type=int, default=None, help="Limit number of visas to scrape (for testing)")
def scrape(skip_enrichment: bool, fresh: bool, limit: int | None):
    """Run the full scraping pipeline: crawl -> parse -> enrich."""
    asyncio.run(_scrape(skip_enrichment, fresh, limit))


async def _scrape(skip_enrichment: bool, fresh: bool, limit: int | None):
    """Execute the scraping pipeline.

    Args:
        skip_enrichment: Skip LLM enrichment phase
        fresh: Reset state and start from scratch
        limit: Maximum number of visas to scrape (None for all)
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
        listing_parser = ListingParser(settings.BASE_URL)
        visa_listings = listing_parser.parse(listing_html)

        logger.info("visa_listings_found", count=len(visa_listings))

        # Apply limit if specified
        if limit:
            visa_listings = visa_listings[:limit]
            logger.info("limit_applied", scraping_count=len(visa_listings))

        # Phase 2: Crawl and parse each visa detail page
        logger.info("phase_2_crawl_visa_details", total=len(visa_listings))

        detail_crawler = DetailCrawler(settings)
        detail_parser = DetailParser()

        for i, listing in enumerate(visa_listings, 1):
            # Check if already completed
            if state_manager.is_completed(listing.visa_url):
                logger.info(
                    "skipping_completed",
                    url=listing.visa_url,
                    progress=f"{i}/{len(visa_listings)}",
                )
                continue

            try:
                # Apply anti-blocking delay (except for first request)
                if i > 1:
                    await random_delay(
                        settings.MIN_DELAY_SECONDS,
                        settings.MAX_DELAY_SECONDS,
                    )

                # Crawl visa detail page
                detail_html = await detail_crawler.crawl(page, listing.visa_url)
                file_manager.save_raw_html(listing.visa_url, detail_html)

                # Parse visa detail page
                visa_data = detail_parser.parse(
                    detail_html,
                    listing.visa_url,
                    listing.category,
                )
                file_manager.save_parsed_json(listing.visa_url, visa_data)

                # Mark as completed
                state_manager.mark_completed(listing.visa_url)

                logger.info(
                    "visa_processed",
                    progress=f"{i}/{len(visa_listings)}",
                    visa=listing.visa_name,
                    url=listing.visa_url,
                )

            except Exception as e:
                logger.error(
                    "visa_processing_failed",
                    url=listing.visa_url,
                    visa=listing.visa_name,
                    error=str(e),
                    progress=f"{i}/{len(visa_listings)}",
                )
                # Continue to next visa (fail loudly but don't abort)
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
        total_visas=len(visa_listings),
    )

    click.echo(f"\n[OK] Scraping completed!")
    click.echo(f"   Visas processed: {stats['completed_count']}/{len(visa_listings)}")
    click.echo(f"   Raw HTML: {settings.RAW_DIR}")
    click.echo(f"   Parsed JSON: {settings.PARSED_DIR}")
    click.echo(f"   Logs: {settings.LOGS_DIR}")


async def _enrich_all(file_manager: FileManager):
    """Enrich all parsed JSONs with LLM classification.

    Args:
        file_manager: FileManager instance
    """
    try:
        from src.enrichment.enricher import VisaEnricher
        from src.enrichment.llm_client import LLMClient

        llm_client = LLMClient(settings)
        enricher = VisaEnricher(llm_client)

        parsed_files = file_manager.get_all_parsed_files()
        logger.info("enriching_visas", count=len(parsed_files))

        for i, file_path in enumerate(parsed_files, 1):
            try:
                # Load parsed visa
                visa_data = file_manager.load_parsed_json(file_path.stem)

                # Enrich with LLM
                enriched_data = await enricher.enrich(visa_data)

                # Save enriched data
                file_manager.save_enriched_json(visa_data.source_url, enriched_data)

                logger.info(
                    "visa_enriched",
                    progress=f"{i}/{len(parsed_files)}",
                    visa=visa_data.visa_name,
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
    click.echo(f"   Completed visas: {stats_data['completed_count']}")
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
@click.option("--port", type=int, default=8000, help="Port to run the server on")
def serve(port: int):
    """Start the web server to view scraped visa data."""
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
