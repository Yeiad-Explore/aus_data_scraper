# Frontend Setup Guide

This project now includes a modern React frontend for browsing and searching scraped visa data.

## Quick Start

### 1. Install Frontend Dependencies

```bash
cd frontend
npm install
```

### 2. Start the Backend API Server

In the project root directory:

```bash
# Option 1: Using the CLI command
python -m src.main serve

# Option 2: Directly run the API server
python -m api.server

# Option 3: Using uvicorn directly
uvicorn api.server:app --reload
```

The API will be available at `http://localhost:8000`

### 3. Start the Frontend Development Server

In the `frontend` directory:

```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

## Features

- **Browse Visas**: View all scraped visas grouped by category
- **Search**: Search by visa name, category, subclass, or summary
- **Detail View**: Click on any visa to see full details including all sections
- **Responsive Design**: Works on desktop and mobile devices
- **Modern UI**: Built with React, Tailwind CSS, and Vite

## API Endpoints

The frontend communicates with the FastAPI backend:

- `GET /api/visas` - Get all visas
- `GET /api/visas/{slug}` - Get visa by slug
- `GET /api/stats` - Get scraping statistics

## Development

### Frontend Structure

```
frontend/
├── src/
│   ├── components/     # React components
│   │   ├── VisaList.jsx
│   │   ├── VisaDetail.jsx
│   │   └── SearchBar.jsx
│   ├── utils/          # Utility functions
│   ├── App.jsx         # Main app component
│   ├── main.jsx        # Entry point
│   └── index.css       # Global styles
├── index.html
├── package.json
└── vite.config.js
```

### Building for Production

```bash
cd frontend
npm run build
```

The built files will be in `frontend/dist/`

## Troubleshooting

### API Connection Issues

- Make sure the backend API is running on port 8000
- Check that CORS is enabled in the API server
- Verify the proxy configuration in `vite.config.js`

### No Data Showing

- Ensure you have scraped some visa data first using `python -m src.main scrape`
- Check that JSON files exist in `data/parsed/` or `data/enriched/`
- Verify the API endpoints are returning data by visiting `http://localhost:8000/api/visas`
