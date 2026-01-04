"""Generic listing data models - interim mapping from listing page."""

from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class ContentListing(BaseModel):
    """Interim mapping from listing page.

    Contains metadata extracted from links on the listing page.
    """

    category: str = ""
    title: str = ""
    url: str = ""


class ListingPageData(BaseModel):
    """All content links discovered from the listing page.

    This is the complete output from parsing the listing page.
    """

    items: List[ContentListing] = Field(default_factory=list)
    scraped_at: datetime = Field(default_factory=datetime.utcnow)

    def __len__(self) -> int:
        """Return the number of items in the listing."""
        return len(self.items)
