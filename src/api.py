"""REST API server for the Generic Web Scraper."""

import asyncio
from typing import Optional

import structlog
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, HttpUrl

from config.logging_config import setup_logging
from config.settings import settings
from src.models.generic import JobConfig, CrawlConfig
from src.generic_scraper import GenericScraper

# Setup logging
setup_logging(log_file=settings.LOGS_DIR / "api.log", console_level="INFO")
logger = structlog.get_logger()

# Create FastAPI app
app = FastAPI(
    title="Generic Web Scraper API",
    description="API for scraping websites with intelligent content extraction",
    version="1.0.0",
)

# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development. Restrict in production!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store for tracking scraping jobs
scraping_jobs = {}


class ScrapeRequest(BaseModel):
    """Request model for scraping endpoint."""

    url: HttpUrl = Field(..., description="Starting URL to scrape")
    name: str = Field(..., description="Job name for this scrape", min_length=1)
    depth: int = Field(default=1, description="Maximum crawl depth", ge=0, le=5)
    max_pages: int = Field(default=50, description="Maximum pages to scrape", ge=1, le=1000)
    filter: str = Field(
        default="same_path",
        description="Link filter strategy",
        pattern="^(same_path|same_domain|all)$"
    )
    save_individual_pages: bool = Field(
        default=True,
        description="Whether to save individual page extractions"
    )
    final_synthesis: bool = Field(
        default=True,
        description="Whether to perform final LLM synthesis"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://immi.homeaffairs.gov.au/entering-and-leaving-australia/entering-australia/overview",
                "name": "entering_australia",
                "depth": 1,
                "max_pages": 10,
                "filter": "same_path",
                "save_individual_pages": True,
                "final_synthesis": True
            }
        }


class ScrapeResponse(BaseModel):
    """Response model for scraping endpoint."""

    status: str
    message: str
    job_id: str
    job_name: str
    url: str


async def run_scraper(job_id: str, request: ScrapeRequest):
    """Run the scraper in the background.

    Args:
        job_id: Unique job identifier
        request: Scrape request parameters
    """
    try:
        logger.info(
            "scrape_job_started",
            job_id=job_id,
            url=str(request.url),
            name=request.name
        )

        # Update job status
        scraping_jobs[job_id]["status"] = "running"

        # Create job configuration
        crawl_config = CrawlConfig(
            depth=request.depth,
            max_pages=request.max_pages,
            link_filter=request.filter
        )

        job_config = JobConfig(
            job_name=request.name,
            start_url=str(request.url),
            crawl_config=crawl_config,
            save_individual_pages=request.save_individual_pages,
            final_synthesis=request.final_synthesis
        )

        # Run the scraper
        scraper = GenericScraper(settings)
        result = await scraper.scrape(job_config)

        # Update job with results
        scraping_jobs[job_id]["status"] = "completed"
        scraping_jobs[job_id]["result"] = {
            "pages_scraped": result.crawl_metadata.get("total_pages", 0),
            "duration_seconds": result.crawl_metadata.get("duration_seconds", 0),
            "output_path": str(settings.DATA_DIR / request.name),
            "failed_urls": result.crawl_metadata.get("failed_urls", [])
        }

        logger.info(
            "scrape_job_completed",
            job_id=job_id,
            pages_scraped=result.crawl_metadata.get("total_pages", 0)
        )

    except Exception as e:
        logger.error(
            "scrape_job_failed",
            job_id=job_id,
            error=str(e)
        )
        scraping_jobs[job_id]["status"] = "failed"
        scraping_jobs[job_id]["error"] = str(e)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Generic Web Scraper API",
        "version": "1.0.0",
        "endpoints": {
            "POST /scrape": "Submit a scraping job",
            "GET /jobs/{job_id}": "Get job status",
            "GET /jobs": "List all jobs",
            "GET /health": "Health check"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Generic Web Scraper API"
    }


@app.post("/scrape", response_model=ScrapeResponse)
async def scrape(request: ScrapeRequest, background_tasks: BackgroundTasks):
    """Submit a scraping job.

    Args:
        request: Scrape request parameters
        background_tasks: FastAPI background tasks

    Returns:
        ScrapeResponse with job details
    """
    # Generate job ID
    import uuid
    job_id = str(uuid.uuid4())

    # Store job info
    scraping_jobs[job_id] = {
        "job_id": job_id,
        "job_name": request.name,
        "url": str(request.url),
        "status": "queued",
        "created_at": None,
        "result": None,
        "error": None
    }

    # Add import for datetime
    from datetime import datetime
    scraping_jobs[job_id]["created_at"] = datetime.utcnow().isoformat()

    # Add scraping task to background
    background_tasks.add_task(run_scraper, job_id, request)

    logger.info(
        "scrape_job_queued",
        job_id=job_id,
        url=str(request.url),
        name=request.name
    )

    return ScrapeResponse(
        status="queued",
        message="Scraping job has been queued and will start shortly",
        job_id=job_id,
        job_name=request.name,
        url=str(request.url)
    )


@app.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get the status of a scraping job.

    Args:
        job_id: Job identifier

    Returns:
        Job status information
    """
    if job_id not in scraping_jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    return scraping_jobs[job_id]


@app.get("/jobs")
async def list_jobs():
    """List all scraping jobs.

    Returns:
        List of all jobs with their status
    """
    return {
        "total": len(scraping_jobs),
        "jobs": list(scraping_jobs.values())
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
