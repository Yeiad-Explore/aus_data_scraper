"""File manager for storing scraped data."""

from pathlib import Path

import structlog

from settings import Settings
from content_models import EnrichedContentData, ContentData
from url_utils import url_to_slug

logger = structlog.get_logger()


class FileManager:
    """Handles all file I/O operations for the scraper.

    Manages storage of raw HTML, parsed JSON, and enriched JSON files.
    """

    def __init__(self, settings: Settings):
        """Initialize file manager.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Create data directories if they don't exist."""
        directories = [
            self.settings.DATA_DIR,
            self.settings.RAW_DIR,
            self.settings.PARSED_DIR,
            self.settings.ENRICHED_DIR,
            self.settings.STATE_DIR,
            self.settings.LOGS_DIR,
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

        logger.debug("directories_ensured", count=len(directories))

    def save_raw_html(self, url: str, html: str) -> Path:
        """Save raw HTML with URL-based filename.

        Args:
            url: Source URL
            html: HTML content

        Returns:
            Path to saved file
        """
        slug = url_to_slug(url)
        file_path = self.settings.RAW_DIR / f"{slug}.html"

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html)

        logger.debug("raw_html_saved", slug=slug, size=len(html), path=str(file_path))

        return file_path

    def save_parsed_json(self, url: str, content: ContentData) -> Path:
        """Save parsed JSON data.

        Args:
            url: Source URL
            content: ContentData object

        Returns:
            Path to saved file
        """
        slug = url_to_slug(url)
        file_path = self.settings.PARSED_DIR / f"{slug}.json"

        content.to_json_file(file_path)

        logger.debug("parsed_json_saved", slug=slug, path=str(file_path))

        return file_path

    def save_enriched_json(self, url: str, enriched: EnrichedContentData) -> Path:
        """Save enriched JSON data.

        Args:
            url: Source URL
            enriched: EnrichedContentData object

        Returns:
            Path to saved file
        """
        slug = url_to_slug(url)
        file_path = self.settings.ENRICHED_DIR / f"{slug}.json"

        enriched.to_json_file(file_path)

        logger.debug("enriched_json_saved", slug=slug, path=str(file_path))

        return file_path

    def load_parsed_json(self, url: str) -> ContentData:
        """Load parsed JSON for enrichment.

        Args:
            url: Source URL

        Returns:
            ContentData object

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        slug = url_to_slug(url)
        file_path = self.settings.PARSED_DIR / f"{slug}.json"

        content = ContentData.from_json_file(file_path)

        logger.debug("parsed_json_loaded", slug=slug, path=str(file_path))

        return content

    def get_all_parsed_files(self) -> list[Path]:
        """Get all parsed JSON file paths.

        Returns:
            List of Path objects
        """
        return list(self.settings.PARSED_DIR.glob("*.json"))

    def load_parsed_json_from_path(self, file_path: Path) -> ContentData:
        """Load parsed JSON from a file path.

        Args:
            file_path: Path to the JSON file

        Returns:
            ContentData object

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        content = ContentData.from_json_file(file_path)
        logger.debug("parsed_json_loaded_from_path", path=str(file_path))
        return content

    def file_exists(self, url: str, file_type: str = "parsed") -> bool:
        """Check if a file already exists for a URL.

        Args:
            url: Source URL
            file_type: Type of file to check ('raw', 'parsed', 'enriched')

        Returns:
            True if file exists, False otherwise
        """
        slug = url_to_slug(url)

        if file_type == "raw":
            file_path = self.settings.RAW_DIR / f"{slug}.html"
        elif file_type == "parsed":
            file_path = self.settings.PARSED_DIR / f"{slug}.json"
        elif file_type == "enriched":
            file_path = self.settings.ENRICHED_DIR / f"{slug}.json"
        else:
            raise ValueError(f"Unknown file type: {file_type}")

        return file_path.exists()
