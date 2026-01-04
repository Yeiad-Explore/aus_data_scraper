"""FastAPI server to serve scraped visa data to the frontend."""

import json
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config.settings import settings
from src.models.visa import EnrichedVisaData, VisaData
from src.utils.url_utils import url_to_slug

app = FastAPI(title="Australian Visa Scraper API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def load_visa_data(slug: str, prefer_enriched: bool = True) -> Optional[dict]:
    """Load visa data by slug.
    
    Args:
        slug: URL slug
        prefer_enriched: If True, try enriched first, then parsed
        
    Returns:
        Visa data as dict or None
    """
    # Try enriched first if preferred
    if prefer_enriched:
        enriched_path = settings.ENRICHED_DIR / f"{slug}.json"
        if enriched_path.exists():
            try:
                with open(enriched_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data
            except Exception:
                pass
    
    # Fall back to parsed
    parsed_path = settings.PARSED_DIR / f"{slug}.json"
    if parsed_path.exists():
        try:
            with open(parsed_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data
        except Exception:
            pass
    
    return None


@app.get("/")
def root():
    """API root endpoint."""
    return {
        "message": "Australian Visa Scraper API",
        "version": "0.1.0",
        "endpoints": {
            "visas": "/api/visas",
            "visa_detail": "/api/visas/{slug}"
        }
    }


@app.get("/api/visas")
def get_all_visas(prefer_enriched: bool = True) -> List[dict]:
    """Get all scraped visas.
    
    Args:
        prefer_enriched: If True, prefer enriched data over parsed
        
    Returns:
        List of visa data
    """
    visas = []
    
    # Collect all parsed files
    parsed_files = list(settings.PARSED_DIR.glob("*.json"))
    enriched_files = {f.stem: f for f in settings.ENRICHED_DIR.glob("*.json")} if settings.ENRICHED_DIR.exists() else {}
    
    for parsed_file in parsed_files:
        slug = parsed_file.stem
        
        # Try enriched first if preferred
        if prefer_enriched and slug in enriched_files:
            try:
                with open(enriched_files[slug], "r", encoding="utf-8") as f:
                    visa_data = json.load(f)
                    visas.append(visa_data)
                    continue
            except Exception:
                pass
        
        # Fall back to parsed
        try:
            with open(parsed_file, "r", encoding="utf-8") as f:
                visa_data = json.load(f)
                visas.append(visa_data)
        except Exception as e:
            print(f"Error loading {parsed_file}: {e}")
            continue
    
    return visas


@app.get("/api/visas/{slug}")
def get_visa_by_slug(slug: str, prefer_enriched: bool = True) -> dict:
    """Get visa data by slug.
    
    Args:
        slug: URL slug
        prefer_enriched: If True, prefer enriched data over parsed
        
    Returns:
        Visa data
    """
    visa_data = load_visa_data(slug, prefer_enriched)
    
    if not visa_data:
        raise HTTPException(status_code=404, detail=f"Visa with slug '{slug}' not found")
    
    return visa_data


@app.get("/api/stats")
def get_stats() -> dict:
    """Get scraping statistics."""
    stats = {
        "parsed_count": len(list(settings.PARSED_DIR.glob("*.json"))) if settings.PARSED_DIR.exists() else 0,
        "enriched_count": len(list(settings.ENRICHED_DIR.glob("*.json"))) if settings.ENRICHED_DIR.exists() else 0,
        "raw_count": len(list(settings.RAW_DIR.glob("*.html"))) if settings.RAW_DIR.exists() else 0,
    }
    return stats


if __name__ == "__main__":
    import sys
    import uvicorn
    
    port = 8000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    
    uvicorn.run(app, host="0.0.0.0", port=port)

