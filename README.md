# LeadScrapper — Lead Intelligence Platform

Web-based lead generation tool built with Python (FastAPI) + React + SQLite. Extracts business contacts from Google Maps or advanced search queries, then cleans, deduplicates, and exports them as CSV.

## Stack

- **Backend**: Python 3.11+, FastAPI, SQLite (WAL mode)
- **Frontend**: React 18, Tailwind CSS, React Router v6
- **Scrapers**: requests + BeautifulSoup (Maps), DuckDuckGo Search (Dorks)

## Setup & Run

### 1. Configure Environment

```bash
cp .env.example .env
```

### 2. API Keys (Optional)

At least one of these enables more reliable scraping:

| Key | Purpose | Free Tier |
|-----|---------|-----------|
| `GOOGLE_MAPS_API_KEY` | Official Places API (most reliable) | $200/mo credit (~28k requests) |
| `SCRAPER_API_KEY` | Handles anti-scraping / CAPTCHAs | 5,000 requests/mo |

If no keys are set, the scraper falls back to DuckDuckGo (free, no key needed).

### 3. Backend

```bash
cd backend
uv add -r requirements.txt
uv run app.py
```

Server: http://localhost:8000 | API docs: http://localhost:8000/docs

### 4. Frontend

```bash
cd frontend
npm install
npm start
```

App: http://localhost:3000

---

## Features

| Feature | Description |
|---------|-------------|
| **Maps Mode** | Searches Google for local businesses by keyword + location. Extracts name, phone, address, website, and rating. |
| **Dorks Mode** | Runs advanced search queries, visits each result page, and extracts emails, phones, and contact info. |
| **Enrichment** | Post-scrape, visits each website to find missing emails, phone numbers, and social media links. |
| **Social Links** | Extracts LinkedIn, Facebook, Twitter/X, Instagram, YouTube, TikTok, Pinterest, GitHub, and Threads profiles. |
| **Export CSV** | Download cleaned leads as CSV, optionally filtered by source, email, or phone presence. |
| **Task Management** | Cancel running tasks, view real-time logs, and track progress. |

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/tasks/maps | Start a Maps scraping task |
| POST | /api/tasks/dorks | Start a Dorks scraping task |
| GET | /api/tasks | List all tasks |
| GET | /api/tasks/{id} | Get task status + progress |
| GET | /api/tasks/{id}/logs | Get task log lines |
| GET | /api/tasks/{id}/results | Get paginated leads |
| GET | /api/tasks/{id}/export | Download CSV |
| POST | /api/tasks/{id}/enrich | Start enrichment |
| POST | /api/tasks/{id}/cancel | Cancel a running task |
| GET | /api/health | Health check |

---

## Project Structure

```
leadScrapper/
├── backend/
│   ├── app.py                    # FastAPI entrypoint
│   ├── api/routes.py             # REST API endpoints
│   ├── core/config.py            # Settings & env vars
│   ├── core/task_manager.py      # Async task orchestration
│   ├── database/db.py            # SQLite connection & schema
│   ├── database/models.py        # Lead/task CRUD operations
│   ├── scraper/maps_scraper.py   # Google Maps / DuckDuckGo scraper
│   ├── scraper/dorks_scraper.py  # Dork-based website scraper
│   ├── parser/extractor.py       # HTML email/phone/social extraction
│   ├── processing/cleaner.py     # Data normalization & validation
│   ├── processing/enricher.py    # Post-scrape website enrichment
│   ├── exporter/csv_exporter.py  # CSV generation with filters
│   └── utils/                    # Helpers, logger, headers
├── frontend/
│   └── src/
│       ├── App.jsx               # Router & layout
│       ├── pages/Dashboard.jsx   # Task creation form
│       ├── pages/Results.jsx     # Task results + logs
│       ├── pages/TaskHistory.jsx # Past tasks list
│       ├── components/           # Reusable UI components
│       ├── hooks/useTaskPoller.js # Real-time task polling
│       ├── services/api.js       # API client
│       └── utils/formatters.js   # Display formatting
├── storage/exports/              # Generated CSV files
└── logs/                         # Task log files
```

---

## Data Flow

1. User submits a task (Maps or Dorks mode) via the dashboard
2. Backend creates a task record and starts async scraping
3. Scraper fetches business listings and visits websites to extract contacts
4. Extracted data (emails, phones, addresses, social links) is cleaned and deduplicated
5. Leads are stored in SQLite and served via paginated API
6. User can export filtered results as CSV or run enrichment to fill missing data
