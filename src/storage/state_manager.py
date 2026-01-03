"""State manager for tracking crawl progress."""

import json
from datetime import datetime
from pathlib import Path
from typing import Set

import structlog

logger = structlog.get_logger()


class StateManager:
    """Tracks crawl progress for resumability.

    Maintains a record of successfully completed URLs so that
    the scraper can resume from where it left off if interrupted.
    """

    def __init__(self, state_dir: Path):
        """Initialize state manager.

        Args:
            state_dir: Directory to store state file
        """
        self.state_dir = state_dir
        self.state_file = state_dir / "crawl_state.json"
        self.completed_urls: Set[str] = set()
        self._load_state()

    def _load_state(self) -> None:
        """Load existing state from file if available."""
        if self.state_file.exists():
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.completed_urls = set(data.get("completed_urls", []))

                logger.info(
                    "state_loaded",
                    completed_count=len(self.completed_urls),
                    state_file=str(self.state_file),
                )
            except Exception as e:
                logger.error("state_load_failed", error=str(e), state_file=str(self.state_file))
                self.completed_urls = set()
        else:
            logger.info("no_existing_state", state_file=str(self.state_file))

    def mark_completed(self, url: str) -> None:
        """Mark URL as successfully scraped.

        Args:
            url: URL that was successfully scraped
        """
        self.completed_urls.add(url)
        self._save_state()

    def is_completed(self, url: str) -> bool:
        """Check if URL has already been scraped.

        Args:
            url: URL to check

        Returns:
            True if URL was already scraped, False otherwise
        """
        return url in self.completed_urls

    def get_completed_count(self) -> int:
        """Get count of completed URLs.

        Returns:
            Number of completed URLs
        """
        return len(self.completed_urls)

    def _save_state(self) -> None:
        """Persist state to disk.

        This is called after each successful scrape to ensure
        progress is saved incrementally.
        """
        self.state_dir.mkdir(parents=True, exist_ok=True)

        data = {
            "completed_urls": list(self.completed_urls),
            "last_updated": datetime.utcnow().isoformat(),
            "total_completed": len(self.completed_urls),
        }

        try:
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            logger.debug("state_saved", completed_count=len(self.completed_urls))

        except Exception as e:
            logger.error("state_save_failed", error=str(e), state_file=str(self.state_file))

    def reset(self) -> None:
        """Clear all state for a fresh run.

        This removes the state file and clears the in-memory state.
        """
        self.completed_urls.clear()

        if self.state_file.exists():
            self.state_file.unlink()

        logger.info("state_reset", state_file=str(self.state_file))

    def get_stats(self) -> dict:
        """Get statistics about current state.

        Returns:
            Dictionary with state statistics
        """
        return {
            "completed_count": len(self.completed_urls),
            "state_file": str(self.state_file),
            "state_file_exists": self.state_file.exists(),
        }
