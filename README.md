# Australian Home Affairs Visa Scraper

A deterministic web scraper for extracting visa information from the Australian Department of Home Affairs website.

## Features

- **Deterministic Scraping**: Non-agent-based, predictable extraction
- **Full-Site Coverage**: Crawls all visa listing categories and detail pages
- **JavaScript Rendering**: Uses Playwright for dynamic content
- **Structured Output**: Clean JSON schema with validation
- **Resumability**: State tracking for interrupted scrapes
- **LLM Enrichment**: Optional post-processing with Claude/OpenAI/Azure
- **Anti-Blocking**: Configurable delays and single browser context
- **Web Frontend**: Interactive web interface to browse visa data

## Architecture

```
Playwright Crawler → DOM Parser → Clean JSON (ground truth)
                                       ↓
                            LLM Post-Processor (optional)
                                       ↓
                                 Enriched JSON
```

## Installation

### Prerequisites

- Python 3.11 or higher
- pip or Poetry

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd immi-scraper
```

2. Install dependencies:
```bash
# Using pip
pip install -e .

# Or using Poetry
poetry install
```

3. Install Playwright browsers:
```bash
playwright install chromium
```

4. Configure environment (optional):
```bash
cp .env.example .env
# Edit .env with your settings
```

## Usage

### Basic Scraping

Scrape all visas (without LLM enrichment):

```bash
python -m src.main scrape --skip-enrichment
```

### Full Pipeline (with LLM)

Configure LLM API key in `.env`:

```bash
LLM_PROVIDER=anthropic  # or "openai"
LLM_API_KEY=sk-ant-...  # your API key
```

Run full pipeline:

```bash
python -m src.main scrape
```

### CLI Commands

#### Scrape

```bash
# Full scrape with LLM enrichment
python -m src.main scrape

# Skip LLM enrichment
python -m src.main scrape --skip-enrichment

# Fresh start (ignore previous state)
python -m src.main scrape --fresh

# Limit for testing (scrape only 10 visas)
python -m src.main scrape --skip-enrichment --limit 10

# Verbose logging
python -m src.main --verbose scrape
```

#### Validate

Validate scraped data:

```bash
# Validate parsed JSON
python -m src.main validate

# Validate enriched JSON
python -m src.main validate --type enriched
```

#### Statistics

View scraping progress:

```bash
python -m src.main stats
```

#### Reset

Reset scraping state (keeps data files):

```bash
python -m src.main reset
```

## Configuration

Configuration is managed via environment variables (`.env`) or settings defaults.

### Key Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `HEADLESS` | `true` | Run browser in headless mode |
| `MIN_DELAY_SECONDS` | `3.0` | Minimum delay between pages |
| `MAX_DELAY_SECONDS` | `6.0` | Maximum delay between pages |
| `PAGE_LOAD_TIMEOUT` | `30000` | Page load timeout (ms) |
| `LLM_PROVIDER` | `anthropic` | LLM provider (`anthropic`, `openai`, or `azure`) |
| `LLM_API_KEY` | - | API key for LLM enrichment |
| `LLM_MODEL` | `claude-3-5-sonnet-20241022` | LLM model to use |

See [.env.example](.env.example) for all available settings.

## Data Schema

### Visa Data (Locked Schema)

All visa data conforms to this schema:

```json
{
  "visa_name": "Skilled Independent visa (subclass 189)",
  "subclass": "189",
  "category": "Work and skilled visas",
  "summary": "This visa lets skilled workers live and work permanently...",
  "sections": [
    {
      "title": "Eligibility",
      "content": "You must be invited to apply..."
    }
  ],
  "source_url": "https://immi.homeaffairs.gov.au/visas/...",
  "scraped_at": "2024-01-15T10:30:00Z"
}
```

### Enriched Data

LLM enrichment adds `section_type` classification:

```json
{
  "sections": [
    {
      "title": "Eligibility",
      "content": "You must be invited to apply...",
      "section_type": "eligibility"
    }
  ]
}
```

**Canonical Section Types:**
- `overview`
- `eligibility`
- `cost`
- `processing_time`
- `duration`
- `work_rights`
- `study_rights`
- `conditions`
- `family`
- `how_to_apply`
- `documents`
- `other`

## Output Structure

```
data/
├── raw/              # Raw HTML files
│   └── visa_slug.html
├── parsed/           # Clean JSON (ground truth)
│   └── visa_slug.json
├── enriched/         # LLM-enhanced JSON
│   └── visa_slug.json
└── state/            # Crawl state for resumability
    └── crawl_state.json
```

## Anti-Blocking Strategy

- **Random Delays**: 3-6 seconds between requests
- **Single Context**: No parallel requests
- **Realistic User-Agent**: Set automatically
- **Retry Logic**: One retry on timeout
- **Respect robots.txt**: Built-in

## Resumability

The scraper tracks progress in `data/state/crawl_state.json`. If interrupted:

1. Simply run `scrape` again - it will skip completed URLs
2. Use `--fresh` to start over
3. Use `reset` to clear state but keep data

## Validation

Validate scraped data:

```bash
python -m src.main validate
```

Checks:
- JSON schema compliance
- Required fields present
- At least one section extracted
- Minimum text length (100 chars)

## Logging

Logs are written to `logs/scraper.log` in structured JSON format.

View logs:

```bash
# Follow logs in real-time
tail -f logs/scraper.log

# Pretty-print JSON logs
cat logs/scraper.log | jq '.'
```

## Development

### Project Structure

```
immi-scraper/
├── config/           # Configuration and logging
├── src/
│   ├── models/       # Data models (Pydantic)
│   ├── crawler/      # Playwright crawlers
│   ├── parser/       # DOM parsers
│   ├── storage/      # File I/O and state
│   ├── enrichment/   # LLM classification
│   ├── utils/        # Utilities
│   └── main.py       # CLI entry point
├── data/             # Output directory
├── tests/            # Unit tests
└── scripts/          # Validation scripts
```

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=src
```

### Code Quality

```bash
# Format code
black .

# Lint
ruff check .

# Type check
mypy src/
```

## Legal & Compliance

This scraper is designed for informational use of publicly available government data.

**Important:**
- Always check and respect `robots.txt`
- Store source URLs for attribution
- Add disclaimers if making data public
- Consult legal counsel before commercial use

## Troubleshooting

### Playwright Installation Issues

```bash
# Reinstall Playwright browsers
playwright install --force chromium
```

### Timeouts

Increase timeouts in `.env`:

```bash
PAGE_LOAD_TIMEOUT=60000
NAVIGATION_TIMEOUT=120000
```

### LLM Enrichment Fails

Check API key is set:

```bash
echo $LLM_API_KEY
```

Skip enrichment if not needed:

```bash
python -m src.main scrape --skip-enrichment
```

## Performance

- **Expected Runtime**: ~200 visas × 5 seconds = ~15-20 minutes
- **Bottleneck**: Intentional delays (anti-blocking)
- **LLM Cost**: ~200 visas × 10 sections × $0.001 = ~$2 (Anthropic)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

[Specify your license here]

## Acknowledgments

- Australian Department of Home Affairs for public visa information
- Playwright for reliable browser automation
- Pydantic for robust data validation

## Support

For issues and questions:
- GitHub Issues: [link]
- Documentation: [link]

---

**Disclaimer**: This is an unofficial tool not affiliated with the Australian Department of Home Affairs. Always verify visa information on the official government website.
