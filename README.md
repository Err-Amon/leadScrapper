# LeadScrapper — Lead Intelligence Platform

Web-based lead generation tool built with Python (FastAPI) + React + SQLite.

## Stack
- **Backend**: Python 3.11+, FastAPI, SQLite (WAL mode)
- **Frontend**: React 18, Tailwind CSS, React Router v6
- **Scrapers**: requests + BeautifulSoup (Maps), googlesearch-python (Dorks)

## Setup & Run

### 1. Environment Configuration

Copy the example environment file and configure your API keys:

```bash
cp .env.example .env
```

### 2. API Keys Setup

#### Option A: Google Maps API (Recommended - Most Reliable)

This is the most reliable method as it uses Google's official API instead of scraping.

**How to get your Google Maps API key:**

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the **Places API (New)**:
   - Navigate to **APIs & Services** > **Library**
   - Search for "Places API (New)" and enable it
4. Create credentials:
   - Go to **APIs & Services** > **Credentials**
   - Click **Create Credentials** > **API Key**
   - Copy your API key
5. (Optional) Restrict the API key to only the Places API for security
6. Add the key to your `.env` file:
   ```
   GOOGLE_MAPS_API_KEY=your-api-key-here
   ```

**Pricing:** Google offers $200 free credit monthly (~28,000 Text Search requests). After that, pay-as-you-go pricing applies.

#### Option B: ScraperAPI (Handles Anti-Scraping)

Use this if you want to scrape Google directly without managing proxies or CAPTCHAs.

**How to get your ScraperAPI key:**

1. Go to [ScraperAPI.com](https://www.scraperapi.com/)
2. Sign up for a free account
3. Navigate to your **Dashboard**
4. Copy your API key
5. Add the key to your `.env` file:
   ```
   SCRAPER_API_KEY=your-api-key-here
   ```

**Pricing:** Free tier includes 5,000 requests/month. Paid plans start at $49/month.

#### Option C: Direct Scraping (No API Key Required)

If no API keys are configured, the scraper will fall back to direct Google scraping. This method is less reliable and may trigger CAPTCHAs.

### 3. Backend

```bash
cd backend
uv add -r requirements.txt
uv run app.py
```

Server starts at: http://localhost:8000
API docs at:      http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
npm start
```

App opens at: http://localhost:3000

---

## API Endpoints

| Method | Endpoint                        | Description                    |
|--------|---------------------------------|--------------------------------|
| POST   | /api/tasks/maps                 | Start a Maps scraping task     |
| POST   | /api/tasks/dorks                | Start a Dorks scraping task    |
| GET    | /api/tasks                      | List all tasks                 |
| GET    | /api/tasks/{id}                 | Get task status + progress     |
| GET    | /api/tasks/{id}/logs            | Get task log lines             |
| GET    | /api/tasks/{id}/results         | Get paginated leads            |
| GET    | /api/tasks/{id}/export          | Download CSV                   |
| GET    | /api/health                     | Health check                   |

---

## Project Structure

```
lead-gen-tool/
├── backend/
│   ├── app.py
│   ├── requirements.txt
│   ├── api/routes.py
│   ├── core/config.py
│   ├── core/task_manager.py
│   ├── database/db.py
│   ├── database/models.py
│   ├── scraper/maps_scraper.py   
│   ├── scraper/dorks_scraper.py  
│   ├── parser/extractor.py
│   ├── processing/cleaner.py
│   ├── processing/enricher.py    
│   ├── exporter/csv_exporter.py
│   └── utils/
├── frontend/
│   └── src/
│       ├── App.js
│       ├── pages/Dashboard.jsx
│       ├── pages/Results.jsx
│       ├── pages/TaskHistory.jsx
│       ├── components/Layout.jsx
│       ├── components/SearchForm.jsx
│       ├── components/ResultsTable.jsx
│       ├── components/ProgressBar.jsx
│       ├── components/LogsPanel.jsx
│       ├── components/ExportButton.jsx
│       ├── hooks/useTaskPoller.js
│       ├── services/api.js
│       └── utils/formatters.js
├── storage/exports/
└── logs/
```


