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
* **Streamlit Dashboard:** `http://localhost:8501` 
* **Prefect Dashboard:** `http://localhost:4200`
---

## Project Structure

```text
nasdaq-intelligence/
├── gx/                       # Great Expectations (GE) configuration
│   ├── checkpoints/          # Checkpoint definitions for validation runs
│   ├── expectations/         # The "prices_suite.json" (Auto-generated)
│   ├── uncommitted/          # Local validation results & HTML Data Docs
│   └── create_suite.py       # Script to define/update rules
├── ingestion/                # Extraction & Loading (EL)
│   ├── fetcher.py            # API calls (yfinance) + local cleaning
│   ├── loader.py             # PostgreSQL interaction (SQLAlchemy/psycopg2)
│   └── pipeline.py           # Prefect flow: fetcher → loader
├── processing/               # Transformation & Validation
│   ├── features.py           # Feature engineering
│   ├── validation.py         # GE Checkpoint execution logic
│   └── pipeline.py           # Prefect flow: validation → feature engineering
├── orchestration/            # Centralized Workflow Management
│   └── flows.py              # Master pipeline: setup → ingestion → processing
├── storage/                  # Database Layer
│   ├── db.py                 # Connection pooling and engine setup
│   └── schema.sql            # Table definitions 
├── ml/                       # Machine Learning Lifecycle
├── models/
├── serving/                  # Output Layer
│   └── dashboard.py            # Streamlit UI for stock visualization
├──serving/
│   ├── dashboard.py          # entry point, just imports and renders pages
│   ├── views/
│       ├── overview.py       # market summary, all 10 tickers at a glance
│       ├── predictions.py    # next-day predictions + actual vs predicted
│       ├── model.py          # model metrics, SHAP, version history
│       └── monitoring.py     # drift detection, MAE trends, pipeline health
└── components/
│       ├── charts.py         # reusable chart functions
│       ├── db.py             # all DB queries for dashboard (read-only)
│       └── theme.py          # colors, styling constants
└──monitoring/
│    ├── drift.py             # data drift + prediction drift detection
│    └── monitor.py           # structured monitoring metrics, logged per run
├── Dockerfile                # Environment definition
├── docker-compose.yml        # Multi-container orchestration (DB, API, Prefect)
├── requirements.txt          # Python dependencies
├── TODO.md                   # Pending tasks
└── .env                      # Local credentials (DO NOT COMMIT)
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
* **Port:** `5433`
* **Database:** `${POSTGRES_DB}`
* **User:** `${POSTGRES_USER}`
* **Password:** `${POSTGRES_PASSWORD}`

### Option 2: Using the Terminal (psql)
You can access the database directly from your terminal using docker exec. Replace the placeholders with your .env values:

```bash
docker exec -it nasdaq-db psql -U <POSTGRES_USER> -d <POSTGRES_DB>
```
---

## 4. Prefect Workflow Orchestration
We use Prefect to schedule and monitor our data pipelines.

### 1. Accessing the Dashboard
Once your Docker containers are running, navigate to: `http://localhost:4200`

This dashboard allows you to track the history of every pipeline run, view logs for individual tasks, and debug failures visually.

### 2. Triggering a Manual Run
The system is set up using a Worker/Deployment model. The nasdaq-pipeline container stays active and waits for instructions.

* In the Prefect UI, go to the **Deployments**tab.
* Find **nasdaq-manual-deployment** (under the nasdaq-master-pipeline flow).
* Click the three dots (options menu) on the right and select **Quick Run**.

### 3. Monitoring & Debugging
If a pipeline run fails:
* Inspect Tasks: Click on the failed run to see exactly which task failed (e.g., fetch_ticker_data).
* View Logs: The UI captures all Python print statements and errors. You can filter logs by "Level" (Info/Error) to find the root cause.
* Retries: We have configured the system to automatically retry failed API calls. You will see these attempts logged in the task history.

---
## 5. Great Expectations
We use Great Expectations (GE) to validate the prices table before processing.
If validation fails, the pipeline stops.
### Where it is defined
* **Expectation suite:** gx/expectations/prices_suite.json
* **Checkpoint config:** gx/checkpoints/prices_checkpoint.yml
* **Execution logic:** processing/validation.py

### How to add a rule:
1.  Open `gx/create_suite.py`.
2.  Locate the `# --- DEFINE EXPECTATIONS ---` section.
3.  Add your new rules using the `validator` object:
```python
# Example: Check for specific ticker formats
 validator.expect_column_values_to_match_regex("ticker", r"^[A-Z]{1,5}$")
```

4.  **Important:** After updating the code, you must delete the old JSON file to let the automation recreate it, or run the script manually:
```bash
docker exec -it nasdaq-pipeline python gx/create_suite.py    
```

### Viewing Validation Reports (Data Docs)
GE generates visual HTML reports for every run. To view them, navigate to `gx/uncommitted/data_docs/local_site/index.html`

### Troubleshooting
* **Empty Suite:** If the `.json` file is empty, delete it and restart the pipeline; the `initialise-ge-suite` task will rebuild it.

---

###  Data Ingestion Flow (End-to-End Logic)

The ingestion pipeline follows a structured flow to ensure both **auditability** and **data quality** before production use:

#### 1. Extraction (The API)
The system uses `yfinance` to fetch raw stock data directly from the web.

#### 2. The Raw Snapshot
The fetched data is first stored in a temporary in-memory variable (`raw_df`). This represents the unaltered dataset exactly as received from the API.

#### 3. Audit Persistence (Table 1: `raw_prices`)
The raw data (`raw_df`) is written directly into the `raw_prices` table.  
This acts as a **“black box recorder”** — preserving all incoming data exactly as it was received.

> Example: If the API returns an invalid value like `-999`, it is still stored here without modification.

#### 4. The Filter (Transformation Layer)
The same `raw_df` is passed through the transformation logic (`clean_ticker_data()` in `transform.py`), where data quality rules are enforced:

- OHLC values must be positive: `OHLC > 0`
- Volume must meet minimum threshold: `Volume >= 100`
- Logical price consistency: `High >= Low`

#### 5. Production Persistence (Table 2: `prices`)
Only the rows that pass all validation checks are written to the `prices` table.

This ensures that:
- `raw_prices` = **complete historical record (including bad data)**
- `prices` = **clean, production-ready dataset**

---