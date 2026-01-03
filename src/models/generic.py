"""
Data models for generic web scraping.
These models support flexible content extraction from any website.
"""

from typing import List, Dict, Any, Optional, Literal
from datetime import datetime
from pydantic import BaseModel, HttpUrl, Field


class CrawlConfig(BaseModel):
    """Configuration for how to crawl a website."""

    depth: int = Field(default=1, ge=0, le=5, description="Maximum crawl depth (0 = only start URL)")
    max_pages: int = Field(default=50, ge=1, le=500, description="Maximum number of pages to scrape")
    link_filter: Literal["same_path", "same_domain", "all"] = Field(
        default="same_path",
        description="How to filter discovered links"
    )
    follow_external: bool = Field(default=False, description="Whether to follow external links")
    expand_accordions: bool = Field(default=True, description="Expand interactive elements")
    accordion_selectors: List[str] = Field(
        default=[
            "button[aria-expanded='false']",
            ".accordion-button.collapsed",
            "[data-toggle='collapse']",
            "details:not([open])",
            ".collapse:not(.show)",
        ],
        description="CSS selectors for accordion elements to expand"
    )
    content_area_selector: Optional[str] = Field(
        default=None,
        description="Optional CSS selector for main content area"
    )


class JobConfig(BaseModel):
    """Configuration for a scraping job."""

    job_name: str = Field(..., description="Unique name for this scraping job")
    start_url: HttpUrl = Field(..., description="Starting URL for the crawl")
    crawl_config: CrawlConfig = Field(default_factory=CrawlConfig)
    save_individual_pages: bool = Field(
        default=True,
        description="Save individual page extractions (for debugging)"
    )
    final_synthesis: bool = Field(
        default=True,
        description="Perform final LLM synthesis of all pages"
    )


class ReferencedLink(BaseModel):
    """A link found in content but not followed."""

    text: str = Field(..., description="Link text/anchor")
    url: str = Field(..., description="Link URL")
    context: Optional[str] = Field(None, description="Surrounding text context")


class InteractiveSection(BaseModel):
    """An interactive section that was expanded (tab, accordion, etc.)."""

    section_type: Literal["tab", "accordion", "details", "other"] = Field(
        default="other",
        description="Type of interactive element"
    )
    section_name: str = Field(..., description="Name/title of the section")
    content: str = Field(..., description="Raw content from the section")
    selector: Optional[str] = Field(None, description="CSS selector used to identify this section")


class GenericPageData(BaseModel):
    """Scraped data from a single page."""

    url: str = Field(..., description="Page URL")
    title: str = Field(..., description="Page title")
    main_content: str = Field(..., description="Main content text")
    interactive_sections: List[InteractiveSection] = Field(
        default_factory=list,
        description="Interactive sections that were expanded"
    )
    referenced_links: List[ReferencedLink] = Field(
        default_factory=list,
        description="Links found in content but not followed"
    )
    discovered_links: List[str] = Field(
        default_factory=list,
        description="Structural links discovered for crawling"
    )
    parent_url: Optional[str] = Field(None, description="Parent page URL")
    depth: int = Field(default=0, description="Depth level from start URL")
    scraped_at: datetime = Field(default_factory=datetime.now, description="Scrape timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class EnrichedPageData(BaseModel):
    """LLM-enriched data from a single page."""

    url: str
    title: str
    content_type: Optional[str] = Field(None, description="LLM-detected content type")
    summary: Optional[str] = Field(None, description="LLM-generated summary")
    structured_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="LLM-extracted structured data"
    )
    parent_url: Optional[str] = None
    depth: int = 0


class CrawlResult(BaseModel):
    """Final result of a crawl job with all pages."""

    job_name: str
    start_url: str
    crawl_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata about the crawl (total pages, duration, etc.)"
    )
    main_page: Optional[EnrichedPageData] = Field(None, description="The starting page data")
    child_pages: List[EnrichedPageData] = Field(
        default_factory=list,
        description="All child pages crawled"
    )
    structured_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Final LLM synthesis of all pages combined"
    )
    crawled_at: datetime = Field(default_factory=datetime.now)


class CrawlState(BaseModel):
    """State tracking for resumable crawls."""

    job_name: str
    start_url: str
    queued_urls: List[str] = Field(default_factory=list, description="URLs to be crawled")
    visited_urls: List[str] = Field(default_factory=list, description="URLs already crawled")
    failed_urls: List[str] = Field(default_factory=list, description="URLs that failed")
    current_depth: int = 0
    total_pages_scraped: int = 0
    last_updated: datetime = Field(default_factory=datetime.now)
