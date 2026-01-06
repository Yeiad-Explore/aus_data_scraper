# Generic Web Scraper - Overview

A modular, async web scraper with LLM-powered content enrichment.

## Quick Start

```bash
pip install -r requirements.txt
playwright install chromium
python run.py https://example.com --name my-job --depth 2
```

## File Descriptions

### Entry Points

| File | Description |
|------|-------------|
| `run.py` | CLI script to run the scraper. Pass URL, job name, depth, and options. |
| `__init__.py` | Package exports for importing as a module. |

### Core Scraper

| File | Description |
|------|-------------|
| `generic_scraper.py` | **Main orchestrator**. Manages the 3-stage pipeline: crawl → parse → enrich. Handles BFS link discovery, page limits, and result synthesis. |
| `browser.py` | Playwright browser manager. Creates browser context with anti-detection headers, viewport, and user agent. |
| `generic_crawler.py` | Page crawler. Navigates to URLs, expands accordions/tabs, scrolls pages, and extracts raw HTML. |
| `generic_parser.py` | HTML parser. Extracts structured content, removes junk (nav, footer, ads), categorizes links, detects interactive sections. |

### LLM Enrichment

| File | Description |
|------|-------------|
| `llm_client.py` | Multi-provider LLM client. Supports **Anthropic Claude**, **OpenAI**, and **Azure OpenAI**. Handles structured data extraction prompts. |
| `generic_enricher.py` | Content enricher. Sends parsed content to LLM for structured extraction, synthesizes multiple pages into final result. |
| `content_models.py` | Content section models with canonical section types (overview, requirements, eligibility, etc.). |

### Storage & State

| File | Description |
|------|-------------|
| `file_manager.py` | File I/O handler. Saves raw HTML, parsed JSON, and enriched JSON to organized directories. |
| `state_manager.py` | Crawl state tracker. Tracks visited/failed URLs for resumable scraping. |

### Utilities

| File | Description |
|------|-------------|
| `models.py` | Pydantic data models: `JobConfig`, `CrawlConfig`, `GenericPageData`, `EnrichedPageData`, `CrawlResult`. |
| `settings.py` | Configuration via environment variables. Reads from `.env` file. |
| `section_detector.py` | Smart link categorizer. Distinguishes structural links (navigation) from referenced links (content). |
| `url_utils.py` | URL normalization and slug generation for filenames. |
| `delays.py` | Random delay utility for anti-blocking (configurable min/max seconds). |
| `logging_config.py` | Structured JSON logging with structlog. |

### Configuration

| File | Description |
|------|-------------|
| `.env` | Environment variables for browser, LLM, timeouts, delays. |
| `requirements.txt` | Python dependencies. |

## Data Flow

```
URL → Browser → Crawler → Parser → Enricher → File Manager
         ↓          ↓         ↓          ↓
      Launch    Expand    Extract    LLM call    Save JSON
      browser   sections  content    for data
```

## Output Structure

```
data/{job-name}/
├── raw_pages/       # Original HTML
├── parsed_pages/    # Structured JSON (no LLM)
├── enriched_pages/  # LLM-enriched JSON
└── final_result.json
```

## Configuration (.env)

```env
# Browser
HEADLESS=false
BROWSER_TYPE=chromium

# Anti-blocking delays
MIN_DELAY_SECONDS=3.0
MAX_DELAY_SECONDS=6.0

# LLM Provider (anthropic, openai, or azure)
LLM_PROVIDER=azure
LLM_API_KEY=your-key
AZURE_OPENAI_ENDPOINT=https://...
AZURE_OPENAI_DEPLOYMENT=gpt-5.1-chat
```
