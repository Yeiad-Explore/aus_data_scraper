# 🌐 Generic Web Scraper

A powerful, deterministic web scraper for extracting structured content from websites with optional LLM-powered enrichment. Submit jobs via REST API or a beautiful web interface.

## ✨ Features

- **🖥️ Web Interface**: Beautiful, user-friendly frontend - no coding required
- **🚀 REST API**: Programmatic access for automation and integration
- **🔄 Smart Crawling**: Intelligent link discovery with depth control
- **📱 JavaScript Support**: Full Playwright browser automation
- **🤖 LLM Enrichment**: Optional content enhancement with Azure OpenAI, Anthropic, or OpenAI
- **📊 Structured Output**: Clean, validated JSON with semantic classification
- **⏸️ Resumable Jobs**: State tracking for interrupted scrapes
- **🛡️ Anti-Blocking**: Configurable delays and realistic browsing patterns
- **📈 Real-time Status**: Track scraping progress with live updates

## 🏗️ Architecture

```
Playwright Browser → Smart Crawler → DOM Parser → Clean JSON
                                                        ↓
                                             LLM Post-Processor (optional)
                                                        ↓
                                                  Enriched JSON
```

## 🚀 Quick Start

### Installation

**Prerequisites:** Python 3.11+

```bash
# 1. Clone the repository
git clone <repository-url>
cd immi-scraper

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install Playwright browsers
playwright install chromium

# 4. (Optional) Configure LLM enrichment
cp .env.example .env
# Edit .env with your Azure OpenAI credentials if you want LLM enrichment
```

### Start the API Server

```bash
python -m src.main api
```

The API will start at `http://localhost:8000`

### Open the Web Interface

Simply open `web/index.html` in your browser:

**Windows:**
```
f:\Work\Personal\immi scraper\web\index.html
```

**Mac/Linux:**
```
file:///path/to/immi-scraper/web/index.html
```

That's it! You can now submit scraping jobs through the web interface. 🎉

## 📖 Usage Guide

### Option 1: Web Interface (Recommended)

The easiest way to use the scraper:

1. **Start the API server:**
   ```bash
   python -m src.main api
   ```

2. **Open the web interface** in your browser:
   - Windows: `f:\Work\Personal\immi scraper\web\index.html`
   - Mac/Linux: `file:///path/to/immi-scraper/web/index.html`

3. **Fill out the form:**
   - Enter the URL to scrape
   - Give your job a name
   - Set crawl depth and max pages
   - Choose link filter strategy
   - Click "Start Scraping"

4. **Monitor progress:**
   - The interface automatically updates every 5 seconds
   - View results when complete

### Option 2: REST API

For programmatic access or automation:

**Submit a job:**
```bash
curl -X POST http://localhost:8000/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "name": "my_job",
    "depth": 1,
    "max_pages": 10,
    "filter": "same_path"
  }'
```

**Check status:**
```bash
curl http://localhost:8000/jobs/{job_id}
```

**View all jobs:**
```bash
curl http://localhost:8000/jobs
```

See the [REST API](#rest-api) section for detailed documentation.

### Option 3: Python Script

```python
import requests

response = requests.post('http://localhost:8000/scrape', json={
    "url": "https://example.com",
    "name": "my_scrape",
    "depth": 1,
    "max_pages": 10,
    "filter": "same_path"
})

job_id = response.json()['job_id']
print(f"Job submitted: {job_id}")
```

See [example_api_usage.py](example_api_usage.py) for a complete example.

## ⚙️ Configuration

### LLM Enrichment (Optional)

To enable AI-powered content classification, configure Azure OpenAI in `.env`:

```bash
LLM_PROVIDER=azure
LLM_API_KEY=your-api-key-here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o
```

**Alternative providers:**
- **Anthropic**: Set `LLM_PROVIDER=anthropic` and `LLM_MODEL=claude-3-5-sonnet-20241022`
- **OpenAI**: Set `LLM_PROVIDER=openai` and `LLM_MODEL=gpt-4o`

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HEADLESS` | `true` | Run browser in headless mode |
| `MIN_DELAY_SECONDS` | `3.0` | Minimum delay between pages |
| `MAX_DELAY_SECONDS` | `6.0` | Maximum delay between pages |
| `PAGE_LOAD_TIMEOUT` | `30000` | Page load timeout (ms) |
| `LLM_PROVIDER` | `azure` | LLM provider (`azure`, `anthropic`, or `openai`) |
| `LLM_API_KEY` | - | API key for LLM enrichment |
| `AZURE_OPENAI_ENDPOINT` | - | Azure endpoint (required if using Azure) |
| `AZURE_OPENAI_DEPLOYMENT` | - | Deployment name (required if using Azure) |
| `LLM_MODEL` | - | Model name (for Anthropic/OpenAI only) |

See [.env.example](.env.example) for all available settings.

### REST API

The scraper provides a REST API for programmatic access. This is the recommended way to submit scraping jobs.

#### Start the API Server

```bash
python -m src.main api
```

Options:
- `--host`: Host to bind to (default: `0.0.0.0`)
- `--port`: Port number (default: `8000`)
- `--reload`: Enable auto-reload for development

The API will be available at `http://localhost:8000`
- API documentation: `http://localhost:8000/docs`
- Alternative docs: `http://localhost:8000/redoc`

#### Submit a Scraping Job

**POST** `/scrape`

Request body:
```json
{
  "url": "https://immi.homeaffairs.gov.au/entering-and-leaving-australia/entering-australia/overview",
  "name": "entering_australia",
  "depth": 1,
  "max_pages": 10,
  "filter": "same_path",
  "save_individual_pages": true,
  "final_synthesis": true
}
```

Example with `curl`:
```bash
curl -X POST http://localhost:8000/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://immi.homeaffairs.gov.au/entering-and-leaving-australia/entering-australia/overview",
    "name": "entering_australia",
    "depth": 1,
    "max_pages": 10,
    "filter": "same_path"
  }'
```

Response:
```json
{
  "status": "queued",
  "message": "Scraping job has been queued and will start shortly",
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "job_name": "entering_australia",
  "url": "https://immi.homeaffairs.gov.au/..."
}
```

#### Check Job Status

**GET** `/jobs/{job_id}`

```bash
curl http://localhost:8000/jobs/123e4567-e89b-12d3-a456-426614174000
```

Response:
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "job_name": "entering_australia",
  "url": "https://...",
  "status": "completed",
  "created_at": "2024-01-15T10:30:00",
  "result": {
    "pages_scraped": 10,
    "duration_seconds": 45.2,
    "output_path": "data/entering_australia",
    "failed_urls": []
  }
}
```

#### List All Jobs

**GET** `/jobs`

```bash
curl http://localhost:8000/jobs
```

#### Python Example

See [example_api_usage.py](example_api_usage.py) for a complete Python example:

```bash
python example_api_usage.py
```

#### Web Frontend

A user-friendly web interface is available for submitting scraping jobs:

1. Start the API server:
```bash
python -m src.main api
```

2. Open the frontend in your browser:
```
file:///path/to/immi-scraper/web/index.html
```

Or on Windows:
```
f:\Work\Personal\immi scraper\web\index.html
```

The frontend provides:
- Simple form to submit scraping jobs
- Real-time status updates
- Results display with scraping statistics
- No curl commands needed!

### CLI Commands

#### Scrape

```bash
# Full scrape with LLM enrichment
python -m src.main scrape

# Skip LLM enrichment
python -m src.main scrape --skip-enrichment

# Fresh start (ignore previous state)
python -m src.main scrape --fresh

# Limit for testing (scrape only 10 pages)
python -m src.main scrape --skip-enrichment --limit 10

# Filter links with pattern
python -m src.main scrape --skip-enrichment --link-pattern "/category/"

# Verbose logging
python -m src.main --verbose scrape
```

#### Generic Scraper

For one-off scraping jobs without modifying settings:

```bash
python -m src.main scrape-generic \
  "https://example.com/start-page" \
  --name my_scrape_job \
  --depth 2 \
  --max-pages 100 \
  --filter same_domain
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

## Data Schema

### Content Data Schema

All scraped content conforms to this schema:

```json
{
  "title": "Product Name",
  "category": "Electronics",
  "summary": "Brief description of the product...",
  "sections": [
    {
      "title": "Specifications",
      "content": "Detailed specifications..."
    }
  ],
  "source_url": "https://example.com/products/...",
  "scraped_at": "2024-01-15T10:30:00Z"
}
```

### Enriched Data

LLM enrichment adds `section_type` classification:

```json
{
  "sections": [
    {
      "title": "Specifications",
      "content": "Detailed specifications...",
      "section_type": "requirements"
    }
  ]
}
```

**Canonical Section Types:**
- `overview`
- `requirements`
- `eligibility`
- `cost`
- `fees`
- `duration`
- `timeline`
- `process`
- `how_to_apply`
- `documents`
- `benefits`
- `conditions`
- `restrictions`
- `related_info`
- `other`

## Output Structure

```
data/
├── raw/              # Raw HTML files
│   └── content_slug.html
├── parsed/           # Clean JSON (ground truth)
│   └── content_slug.json
├── enriched/         # LLM-enhanced JSON
│   └── content_slug.json
└── state/            # Crawl state for resumability
    └── crawl_state.json
```

## Anti-Blocking Strategy

- **Random Delays**: 3-6 seconds between requests (configurable)
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
generic-scraper/
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

This scraper is designed for ethical web scraping of publicly available data.

**Important:**
- Always check and respect `robots.txt`
- Store source URLs for attribution
- Add disclaimers if making data public
- Respect website terms of service
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

- **Runtime**: Depends on number of pages and delay settings
- **Bottleneck**: Intentional delays (anti-blocking)
- **LLM Cost**: Varies by provider and number of sections

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

[Specify your license here]

## Acknowledgments

- Playwright for reliable browser automation
- Pydantic for robust data validation

## Support

For issues and questions:
- GitHub Issues: [link]
- Documentation: [link]

---

**Disclaimer**: This tool is for educational and research purposes. Always respect website terms of service and use responsibly.
