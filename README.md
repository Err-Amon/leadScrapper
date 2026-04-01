# LeadScrapper — Lead Intelligence Platform

Web-based lead generation tool built with Python (FastAPI) + React + SQLite.

## Stack
- **Backend**: Python 3.11+, FastAPI, SQLite (WAL mode)
- **Frontend**: React 18, Tailwind CSS, React Router v6
- **Scrapers**: requests + BeautifulSoup (Maps), googlesearch-python (Dorks)


## Setup & Run

### Backend

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


