# Nasdaq Stock Intelligence System

An end-to-end pipeline designed to ingest, process, and predict NASDAQ stock performance. This system utilizes a containerized **ELT (Extract, Load, Transform)** architecture to ensure environment parity and production-grade reliability.

---

## Getting Started

### 1. Prerequisites
* Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) (ensure it is running).
* Install the **Docker** extension in VS Code for easier container management.

### 2. Environment Configuration
Create a `.env` file in the root directory. You can use the values below (or copy from `.env.example`):

```env
POSTGRES_DB=nasdaq_db
POSTGRES_USER=admin
POSTGRES_PASSWORD=password123
DATABASE_URL=postgresql://admin:password123@db:5432/nasdaq_db
```

### 3. Launch Infrastructure
Run the following command to build and start all services:

```bash
docker-compose up --build
```

**Service Endpoints:**
* **API:** `http://localhost:8000` (FastAPI + Swagger Docs)
* **Dashboard:** `http://localhost:8501` (Streamlit)
* **Prefect Dashboard:** `http://localhost:4200`
---

## Project Structure

```text
nasdaq-intelligence/
├── ingestion/
    ├── fetcher.py       # yfinance calls, returns clean DataFrames
    ├── loader.py        # writes DataFrames to PostgreSQL
    └── pipeline.py      # Prefect flow wiring fetcher → loader
├── processing/           # Feature engineering & validation (Great Expectations)
├── storage/              # Database schemas & SQLAlchemy helpers
├── ml/                   # Model training, evaluation, registry
├── orchestration/        # Prefect flows & scheduling
├── serving/              # FastAPI backend & Streamlit dashboard
├── monitoring/           # Structured logging (JSON)
├── docker-compose.yml    # Multi-container setup
├── Dockerfile            # Python environment definition
├── .env                  # Local credentials (DO NOT COMMIT)
└── requirements.txt      # Python dependencies
```

## Docker Cheat Sheet

### 1. Managing Containers
* **Start (Background):** `docker-compose up -d`
* **Stop & Remove:** `docker-compose down`
* **View Real-time Logs:** `docker-compose logs -f`
* **Check Health:** `docker ps`

### 2. Maintenance & Updates
* **New Dependencies:** Add to `requirements.txt`, then run `docker-compose up --build`.
* **Hard Reset:** `docker-compose down -v` (Removes containers and **all database data**).
* **Shell Access:** `docker exec -it nasdaq-pipeline bash`
* **Schema Changes:** If you modify `storage/schema.sql`, you must run `docker-compose down -v` followed by `docker-compose up --build` for the changes to apply to the database initialization. This will wipe the empty DB and re-initialize it.
* To run a script within the containerized environment: `docker exec -it nasdaq-pipeline python ingestion/fetch.py`
---

## How to View the Data

You can inspect the database tables and data using either a GUI app or the terminal.

### Option 1: Database GUI
Download [DBeaver](https://dbeaver.io/) or [TablePlus](https://tableplus.com/). Use the credentials defined in your .env file:

* **Host:** `localhost`
* **Port:** `5432`
* **Database:** `${POSTGRES_DB}`
* **User:** `${POSTGRES_USER}`
* **Password:** `${POSTGRES_PASSWORD}`

### Option 2: Using the Terminal (psql)
You can access the database directly from your terminal using docker exec. Replace the placeholders with your .env values:

```bash
docker exec -it nasdaq-db psql -U <POSTGRES_USER> -d <POSTGRES_DB>
```
---
