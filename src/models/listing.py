"""Visa listing data models - interim mapping from listing page."""

from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class VisaListing(BaseModel):
    """Interim mapping from visa listing page.

    Contains metadata extracted from visa cards on the listing page.
    """

    category: str = ""
    visa_name: str = ""
    subclass: str = ""
    visa_url: str = ""


class ListingPageData(BaseModel):
    """All visas discovered from the listing page.

    This is the complete output from parsing the visa listing page.
    """

    visas: List[VisaListing] = Field(default_factory=list)
    scraped_at: datetime = Field(default_factory=datetime.utcnow)

    def __len__(self) -> int:
        """Return the number of visas in the listing."""
        return len(self.visas)
