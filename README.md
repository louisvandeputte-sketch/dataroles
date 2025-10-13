# DataRoles

A job aggregation platform that collects, normalizes, and stores job postings from LinkedIn via Bright Data scraper API.

## Architecture

- **Database**: Supabase (PostgreSQL)
- **Backend**: Python 3.11+ with FastAPI
- **Scraping**: Bright Data LinkedIn Jobs Scraper (dataset: gd_lpfll7v5hcqtkxl6l)
- **Frontend**: HTML + Tailwind CSS + Alpine.js
- **Deployment**: Cloud-ready architecture with local development support

## Project Structure

```
dataroles/
├── config/          # Configuration and settings
├── database/        # Database schema and client
├── models/          # Pydantic data models
├── clients/         # External API clients (Bright Data)
├── ingestion/       # Data processing and normalization
├── scraper/         # Scrape orchestration and lifecycle
├── web/             # FastAPI web interface
├── utils/           # Shared utilities
└── tests/           # Test suite
```

## Setup

### 1. Prerequisites

- Python 3.11 or higher
- Supabase account and project
- Bright Data account with LinkedIn Jobs Scraper access

### 2. Installation

```bash
# Clone the repository
cd dataroles

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials
# - SUPABASE_URL and SUPABASE_KEY
# - BRIGHTDATA_API_TOKEN
```

### 4. Database Setup

Execute the database schema in your Supabase SQL editor:

```bash
# Copy contents of database/schema.sql and run in Supabase SQL Editor
```

### 5. Run the Application

```bash
# Start the web interface
python -m uvicorn web.app:app --reload --host 0.0.0.0 --port 8000

# Access at http://localhost:8000
```

## Development

### Running Tests

```bash
pytest
pytest --cov=. --cov-report=html
```

### Mock Mode

For development without consuming Bright Data credits:

```bash
# In .env
USE_MOCK_API=true
```

## Features

- **Job Scraping**: Automated LinkedIn job collection via Bright Data
- **Data Normalization**: Standardized job posting format
- **Deduplication**: Intelligent duplicate detection
- **Web Interface**: Admin dashboard for managing scrape runs
- **Monitoring**: Track scrape status and job statistics
- **LLM-Ready**: Schema prepared for future AI enrichment

## License

Proprietary
