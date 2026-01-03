# Australian Home Affairs Visa Scraper — Plan

## 1. Objective

Build a **deterministic, full-site web scraper** for the Australian Department of Home Affairs visa listing pages that:

- Visits all visa listing categories
- Visits every individual visa detail page
- Scrapes **all visible textual content**
- Stores raw and parsed data
- Optionally enriches parsed data using an LLM **only after scraping**

This project is **not an agent**, **not interactive**, and **not decision-based**.

---

## 2. Scope & Crawl Boundaries

### Entry Point

```

[https://immi.homeaffairs.gov.au/visas/getting-a-visa/visa-listing](https://immi.homeaffairs.gov.au/visas/getting-a-visa/visa-listing)

```

### Allowed URLs

- `/visas/getting-a-visa/visa-listing`
- `/visas/getting-a-visa/visa-listing/*`
- Individual visa detail pages under `/visas/`

### Disallowed Actions

- No form submissions
- No login or authentication
- No navigation outside `/visas/`
- No inferred or guessed data

---

## 3. Data Contract (Locked Schema)

Each visa must produce exactly **one JSON file**:

```json
{
  "visa_name": "",
  "subclass": "",
  "category": "",
  "summary": "",
  "sections": [
    {
      "title": "",
      "content": ""
    }
  ],
  "source_url": "",
  "scraped_at": "ISO-8601"
}
```

Rules:

- Missing fields → empty string or empty array
- No hallucination
- No inference
- Raw text only at this stage

---

## 4. Rendering & Scraping Strategy

### Technology Choice

- **Playwright (Headed/Headless Chromium)**

### Rationale

- JavaScript-rendered content
- Expandable accordions
- Lazy-loaded sections
- DOM consistency post-hydration

`requests + BeautifulSoup` alone is insufficient.

---

## 5. High-Level Architecture

```
Playwright Crawler
   ↓
Raw HTML Storage
   ↓
Deterministic DOM Parser
   ↓
Clean Parsed JSON (Ground Truth)
   ↓
(Optional) LLM Post-Processor
   ↓
Enriched JSON
```

The LLM layer is strictly downstream.

---

## 6. Crawl Flow (Deterministic)

1. Load visa listing page
2. Extract all visa categories
3. Extract all visa card URLs
4. Deduplicate URLs
5. For each visa URL:

   - Load page
   - Wait for hydration
   - Expand all collapsible sections
   - Scroll once (trigger lazy load)
   - Extract structured text
   - Save raw HTML + parsed JSON

No branching logic. No retries beyond one attempt.

---

## 7. Listing Page Extraction

From the listing page, extract:

- Visa category name
- Visa card title
- Visa subclass (if visible)
- Visa detail page URL

Store interim mapping:

```json
{
  "category": "",
  "visa_name": "",
  "visa_url": ""
}
```

---

## 8. Visa Detail Page Extraction

### Required Actions

- Wait for DOM hydration
- Expand all accordions / “read more” sections
- Ignore navigation, footer, breadcrumbs, sidebar

### Data Rules

- Extract all visible text sections
- Preserve section headings exactly
- Do not hardcode section names
- Do not summarize or modify content

---

## 9. Text Cleaning Rules

Allowed:

- Preserve paragraphs
- Preserve bullet points (`-`)
- Preserve line breaks

Remove:

- Cookie banners
- Repeated whitespace
- Navigation junk
- “Back to top” text

---

## 10. Anti-Blocking Strategy

- 3–6 second delay between pages
- Single browser context
- No parallel requests
- No proxy rotation unless blocked
- Respect robots.txt

---

## 11. Storage Strategy

### Directory Structure

```
/data
  /raw
    visa_slug.html
  /parsed
    visa_slug.json
  /enriched
    visa_slug.json
```

### Rules

- Raw HTML is mandatory
- Parsed JSON is derived
- Enriched JSON is optional
- Re-running overwrites existing files
- URL is the unique identifier

---

## 12. Failure Handling

| Scenario        | Action      |
| --------------- | ----------- |
| Timeout         | Retry once  |
| Blocked         | Abort run   |
| Missing DOM     | Log & skip  |
| Partial extract | Save anyway |

Failures must fail loudly.

---

## 13. Validation & QA

Automated checks:

- Visa URL reachable
- At least one section extracted
- Text length above minimum threshold
- JSON validity

Manual spot-check: 5–10 random visas.

---

## 14. LLM Integration (Optional & Controlled)

### Purpose of LLM

The LLM is used **only after scraping** for:

- Section classification
- Schema normalization
- Bullet/list structuring
- Change detection (future runs)

The LLM **never**:

- Navigates pages
- Extracts HTML
- Infers missing data
- Rewrites content

---

## 15. LLM Boundary (Hard Rule)

```
SCRAPER → PARSER → CLEAN JSON
               ↓
          LLM POST-PROCESSOR
               ↓
         ENRICHED JSON
```

The clean JSON is the **ground truth**.

---

## 16. Canonical Section Types (Locked Enum)

```
overview
eligibility
cost
processing_time
duration
work_rights
study_rights
conditions
family
how_to_apply
documents
other
```

LLM must choose **only** from this list.

---

## 17. LLM Prompt Rules

- Temperature = 0
- JSON-only output
- No rewriting content
- No inference
- If unsure → `other`

---

## 18. Change Detection (Optional)

On re-scrape:

- Compare old vs new section content
- Classify change type:

  - wording
  - eligibility
  - cost
  - duration
  - none

Used for alerts, audits, and versioning.

---

## 19. Idempotency Rules

- Multiple runs produce same output for same input
- No duplicate records
- Files are overwritten, not appended
- URLs uniquely identify visas

---

## 20. Legal & Compliance Notes

- Government data for informational use
- Always store source URLs
- No resale without legal review
- Add disclaimer if data is public-facing

---

## 21. Non-Goals

This project does NOT include:

- Chatbots
- Agents
- Reasoning systems
- User interaction
- Recommendation logic

---

## 22. Definition of Done

✔ All visas scraped
✔ Raw HTML stored
✔ Parsed JSON valid
✔ Optional LLM enrichment complete
✔ Re-runnable without duplication

---

End of plan.

```

```
