# TODO


**Task 1.0:** Strengthen `prices` Cleaning Rules  
**Owner:** `[Rubina]` | **Start:** `2024-05-23` | **Status:**  *Complete*

Upgrade the ingestion pipeline with strict validation before `prices` insertion. Maintain `raw_prices` as an immutable audit log.
*   **Target File:** `ingestion/fetcher.py`
*   **Target Function:** `clean_ticker(df)`
*   **Current State:** Only removes NaNs and `close <= 0`.


- [\] **1.1 Null Handling:** Drop row if `open`, `high`, `low`, `close`, or `volume` is NULL.
- [\] **1.2 Price Consistency:** Drop if `high < low`, `high < open/close`, or `low > open/close`.
- [\] **1.3 Positive Constraints:** All OHLCV values must be `> 0`.
- [\] **1.4 Outlier Filter:** Drop rows where `abs(daily_return) > 0.5`.
- [\] **1.5 Deduplication:** Strict uniqueness on `(date, symbol)`.
- [\] **1.6 Open Discovery:** *Add additional data constraints as identified during implementation.*
- [\] **1.7 Audit Integrity:** Ensure `raw_prices` is untouched.
- [\] 1.8 Volume sanity: Drop rows where volume < 100

---

**Task 2.0: Expand Great Expectations Suite** **Owner:** `[Rubina]` | **Start:** `2026-04-` | **Status:** *In Progress*

Implement comprehensive data quality gates using the Great Expectations framework.
* **Target File:** `gx/create_suite.py`
* **Target Function:** `create_nasdaq_suite()`
* **Current State:** Basic boilerplate with only a `not_null` check on `close`.

- [ ] **2.1 Schema Enforcement:** Validate column existence and data types (e.g., `ticker` as string, `volume` as integer).
- [ ] **2.2 Range & Boundary Checks:** Define realistic bounds for prices, volumes, and date ranges.
- [ ] **2.3 Statistical Sanity:** (Optional) Implement expectations for row counts or mean price shifts to catch ingestion gaps.
- [ ] **2.4 Relationship Validation:** Check for cross-column logic (e.g., `high >= low`).
- [ ] **2.5 Set Membership:** Verify that `ticker` values belong to the expected NASDAQ universe.
- [ ] **2.6 Uniqueness Constraints:** Enforce strict uniqueness on the primary key pair `(date, symbol)`.
- [ ] **2.7 Open Discovery:** *Identify and implement additional expectations based on exploratory data analysis (EDA)*
- [ ] **2.8 Documentation:** Ensure all new rules include clear failure messages for the Prefect logs.
  
---
**Task 3.0: ML Model Training & Prediction** **Owner:** `[]` | **Start:** `2026-04-` | **Status:** *Pending*
Build the full ML layer — training, evaluation, and prediction generation — integrated into the existing Prefect pipeline.

**What's already built that your code must work with:**

The monitoring layer (`monitoring/drift.py`, `monitoring/monitor.py`) and serving layer (`serving/`) are already implemented and running. They read from specific tables and files. Your ML code must produce outputs that match exactly.

**`model_registry` table inserts:**
- `symbol` = `'GLOBAL'` always — we have one global model, not per ticker
- `model_version` = `model_v1`, `model_v2` etc. — increment based on existing row count
- `is_champion` = `TRUE` for the best model, `FALSE` for challengers
- `trained_on_data_until` = max date in features table at time of training
- `model_path` = full path to the saved `.pkl` file

**`predictions` table inserts:**
- One row per ticker per pipeline run
- `predicted_close` populated immediately
- `actual_close` = NULL on insert (gets backfilled automatically next day)
- `model_version` = the champion's version string

**`/app/models/champion.pkl`:**
Must be saved using `pickle.dump` as a Python dict with these exact keys:
```
{
    "model":           <trained XGBoost model object>,
    "feature_cols":    <list of all feature column names in training order>,
    "ticker_cols":     <list of one-hot encoded ticker column names only>,
    "shap_importance": <dict mapping feature name → float importance score>,
    "metrics":         {"rmse": float, "mae": float, "r2": float}
}
```
The dashboard loads this file directly to display SHAP charts and metrics. If keys are missing or named differently, the dashboard breaks.

**Versioned model files:**
- `/app/models/model_vX.pkl` — same dict structure as champion.pkl
- `/app/models/metrics_model_vX.json` — JSON file with metrics and SHAP


**What we're building:**
A single global XGBoost regression model that predicts next-day closing price for all 10 NASDAQ tickers. One model, not 10 separate models.A global model learns shared market patterns across all tickers — momentum, volatility regimes, mean reversion — that a per-ticker model can't see. It also avoids the problem of individual tickers having insufficient training data.

**What the model predicts:**
`target` column in the `features` table = next trading day's closing price (already computed as `close.shift(-1)` per ticker during feature engineering).

**Input features:**
- `ma_7` — 7-day moving average
- `ma_21` — 21-day moving average
- `rsi_14` — Relative Strength Index (momentum)
- `daily_return` — % price change (solves multicollinearity between raw OHLCV)
- `volatility_7` — 7-day rolling std of returns (risk signal)
- One-hot encoded `symbol` — so the model knows which ticker it's predicting

Raw ticker names are strings — XGBoost can't use them directly. One-hot encoding creates binary columns like `ticker_AAPL=1, ticker_MSFT=0` etc. This lets the model learn ticker-specific patterns while still training on all data together. Always sort by date first, then split 80% train / 20% test. Never shuffle. This is time-series data — shuffling causes data leakage (future data leaking into training).

**Where data lives:**
- Input: `features` table in PostgreSQL
- Output models: `/app/models/` (Docker volume, already mounted)
- Output predictions: `predictions` table in PostgreSQL

**How to connect to DB:**
```python
from storage.db import engine  # already configured, just import
```
**PYTHONPATH is already set to `.`** in Docker so all imports work from project root.

**Target Files:**
*   ml/trainer.py 
*   ml/predictor.py 
*   ml/pipeline.py — replace the existing stub
*   
### Subtasks
- [ ] **3.0.1 Create `ml/trainer.py:`**
    - Fetch entire `features` table from PostgreSQL
    - Drop rows where any feature or target is NULL
    - One-hot encode `symbol` using `pd.get_dummies` with prefix `"ticker"`
    - Final feature list = 5 numeric features + all `ticker_` columns, in that order
    - Sort by date, split 80/20 without shuffling
    - Train XGBoost regressor
    - Evaluate on test set: RMSE, MAE, R²
    - Log all three metrics
    - Save model to `/app/models/champion.pkl` following the exact dict structure in the contract above:
      - the model object,
      - the list of feature column names,
      - the ticker column names,
      - and the metrics
    - Insert one row into `model_registry` following the contract above
        - `model_version` (use "model_v1" for now; Task 3.1 will make this dynamic),
        - `symbol` = 'GLOBAL',
        - RMSE/MAE/R² values,
        - `is_champion` = TRUE,
        - `trained_on_data_until` = max date in features,
        - and the model path.
    - `model_version` = `"model_v1"` for now — Task 3.1 makes this dynamic

- [ ] **3.0.2 Create `ml/predictor.py`**

    - Load `/app/models/champion.pkl` — if missing, log warning and return empty list
    - Fetch most recent feature row per ticker from `features` table using `DISTINCT ON (symbol)` ordered by date DESC
    - One-hot encode symbol the same way as training
    - For any `ticker_` column present in saved model but missing from current data, fill with 0 — this handles column alignment
    - For each ticker run `model.predict()` on its feature row
    - Compute next trading day date — skip weekends
    - Insert into `predictions` table following the contract above - one row per ticker with date, symbol, predicted_close, model_version,  Use ON CONFLICT (`date`, `symbol`) DO NOTHING so re-running is safe
    - After all predictions inserted, run backfill: update `actual_close` in `predictions` from `prices` where `actual_close IS NULL` and matching price row exists

- [ ] **3.0.3 Update `ml/pipeline.py`**
    - Replace existing stub entirely
    - Prefect `@task` for training that calls trainer.py with `retries=1, retry_delay_seconds=30`
    - Prefect `@task` for prediction that calls predictor.py with `retries=2, retry_delay_seconds=15`
    - Prefect `@flow` named `"nasdaq-ml-pipeline"`
    - Flow must return the training result dict — this gets passed to monitoring
    - Return dict must contain at minimum: `version`, `rmse`, `mae`, `r2`, `is_champion` so orchestration/flows.py can pass it to monitoring.
  
- [ ] **3.0.4 Update `orchestration/flows.py`**
    - Import `ml_flow` from `ml/pipeline.py`
    - Uncomment `ml_flow()` call in `master_pipeline`
    - Capture return value and pass to `task_monitor(train_result)`

- [ ] **3.0.5 Verify end-to-end`**
    - Run full pipeline via Prefect UI.
    - Confirm `model_registry` has one row with `is_champion = TRUE`.
    - Confirm predictions has 10 rows (one per ticker) for next trading day. `SELECT * FROM predictions LIMIT 10;`
    - Confirm docker logs nasdaq-pipeline show RMSE/MAE/R² logged. `docker logs nasdaq-pipeline`
    - `docker exec -it nasdaq-pipeline ls /app/models/` → `champion.pkl` exists

---
**Task 3.1: Advance Extension** **Owner:** `[]` | **Start:** `2026-04-` | **Status:** *Pending* 
**Depends on:** Task 3.0 complete

**What this task adds on top of Task 3.0:**

- [ ] **Champion/Challenger:**
  - Every pipeline run retrains the model.
  - Only deploys a new model if it performs better than the current champion.
  - The current best model is called the *champion*.
  - A newly trained model is called the *challenger*.
  - If challenger RMSE < champion RMSE → challenger becomes the new champion.
  - Otherwise, the old champion stays.
  - `champion.pkl` always contains the best model so far.

- [ ] **Model versioning:**
  - Each trained model is saved as `model_v1.pkl`, `model_v2.pkl`, etc.
  - Provides a full audit trail.
  - Corresponding metrics are saved in `metrics_vX.json` files.

- [ ] **SHAP feature importance:**
  - Compute SHAP values after training to explain feature influence.
  - Save SHAP importance inside `champion.pkl` for dashboard display.

- [\] **Drift detection:**
  Already implemented. File: `monitoring/drift.py`
  - Data drift: using PSI; significant if >0.2.
  - Prediction drift: comparing rolling MAE over different periods; degradation if recent MAE exceeds longer-term MAE by >30%.
  - Results logged in `monitoring_logs` table and read by Streamlit page.

- [ ] **Existing components (do not rebuild):**
  - Logging setup in `monitoring/logger.py`
  - `monitoring_logs` table schema in `schema.sql`
  - Streamlit monitoring page reading from logs
  - Monitoring function call in `flows.py`

**What's done:**
- `monitoring/drift.py` — PSI drift detection + prediction drift. 
- `monitoring/monitor.py` — monitoring orchestrator, writes to `monitoring_logs`. 
- `monitoring/logger.py` — JSON logging setup. 
- `monitoring_logs` table — already in `schema.sql`
- Streamlit monitoring page — reads from `monitoring_logs`
- `task_monitor()` in `orchestration/flows.py` — already calls `run_monitoring()`

**Your job in this task is:**
1. Make the ML trainer smarter (champion/challenger + versioning + SHAP)
2. Verify the existing monitoring code works correctly with your ML output
3. Fix any integration issues between your ML output and the monitoring layer

**Same output contract from Task 3.0 applies** — `champion.pkl` structure, `model_registry` conventions, `predictions` table format. Task 3.1 only adds on top, never changes the contract.


**Champion/Challenger:**
Task 3.0 blindly saves every new model as champion. Task 3.1 makes it smarter — only promote a new model if its RMSE is better than the current champion's RMSE. This means `champion.pkl` always contains the best model ever seen, not just the most recently trained one. The demotion and promotion must happen atomically — in a single database transaction. This prevents a window where no champion exists, which would break predictions.
Every trained model gets a versioned file (`model_v1.pkl`, `model_v2.pkl`) regardless of whether it becomes champion. This creates a full audit trail. A metrics JSON is saved alongside each.

**SHAP feature importance:**
XGBoost is a black box — RMSE tells you how accurate it is but not why it makes predictions. SHAP (SHapley Additive exPlanations) assigns an importance score to each input feature. We compute mean absolute SHAP values across the test set — this tells us globally which features drive predictions most.

This is displayed as a bar chart in the Streamlit Model Registry page. The page loads SHAP directly from `champion.pkl` — which is why the `shap_importance` key must exist in the saved payload.

**Drift detection (implemented):**
`monitoring/drift.py` already handles both data drift (PSI on feature distributions) and prediction drift (rolling MAE comparison). Task is to make sure your ML output is compatible so monitoring runs correctly.


### Subtasks

- [ ] **3.1.1 Add champion/challenger to `ml/trainer.py`**
    - Champion promotion criteria:
      - Condition 1: new model RMSE < current champion RMSE
      - Condition 2: new model MAE <= current champion MAE × 1.05
            (5% tolerance — accounts for statistical noise between runs)
      - Both conditions must be true to promote
      - If no champion exists: always promote regardless of metrics
      - If only one condition met: challenger is saved and versioned
         but champion.pkl is NOT overwritten
    - Champion promotion must be atomic: UPDATE old champion `is_champion = FALSE` and INSERT new row `is_champion = TRUE` in the same `engine.begin()` block
    - Dynamic version: count rows in `model_registry` where `symbol = 'GLOBAL'`, version = `model_v{count+1}`
    - Log clearly which condition failed if promotion is rejected:
         e.g. "Challenger rejected: RMSE improved but MAE worsened by 8%"
   
- [ ] **3.1.2 Add versioned saves to `ml/trainer.py`**
    - Always save `/app/models/model_vX.pkl` regardless of champion status — same dict structure as `champion.pkl`
    - Always save `/app/models/metrics_model_vX.json` — must contain: version, rmse, mae, r2, shap_importance, trained_on date, train row count, test row count
    - Only overwrite `/app/models/champion.pkl` if new model is champion

- [ ] **3.1.3 Add SHAP to `ml/trainer.py`**
    - After training, compute SHAP values using `shap.Explainer`
    - Use max 500 rows from test set for speed
    - Compute mean absolute SHAP value per feature column
    - Result is a dict: `{feature_name: float, ...}` covering all features including `ticker_` columns
    - Add `shap_importance` key to `champion.pkl` payload — required, dashboard reads this
    - Add to metrics JSON file
    - Log top 3 most important features
    - Verify `shap` is in `requirements.txt` before assuming it's installed

- [ ] **3.1.4 Verify `monitoring/drift.py` works with your ML output**
    - Read `monitoring/drift.py` in full before this step
    - After a full pipeline run with predictions generated, run: `docker exec -it nasdaq-pipeline python -c "from monitoring.drift import detect_data_drift, compute_prediction_drift; print(detect_data_drift()); print(compute_prediction_drift())"`
    - `detect_data_drift()` should return real PSI scores — does not need ML, just features table
    - `compute_prediction_drift()` will return NULLs until `actual_close` is backfilled (next day) — this is expected, not a bug
    - If either function crashes, fix the integration issue — do not rewrite the function

- [ ] **3.1.5 Verify `monitoring/monitor.py` writes to DB correctly**
    - Read `monitoring/monitor.py` in full before this step
    - After full pipeline run: `SELECT * FROM monitoring_logs ORDER BY run_at DESC LIMIT 1;`
    - Should show: real `drift_score`, real `drift_detected`, `predictions_made = 10`, `model_version` populated
    - `mae_7d` and `mae_30d` will be NULL until actuals are backfilled — expected
    - If row is missing entirely, check `task_monitor()` is not commented out in `orchestration/flows.py`
    - If crashes, fix integration — do not rewrite `monitor.py`

- [ ] **3.1.6 Verify Streamlit dashboard shows ML data**
    - Go to `localhost:8501` → Model Registry page
    - Champion banner should show model version, RMSE, MAE, R²
    - SHAP chart should show feature importance bars
    - Go to Monitoring page — drift status and predictions count should be real values
    - Go to Predictions page — predicted closes should appear for all 10 tickers

- [ ] **3.1.7 Full end-to-end verification**
    - Run pipeline twice (trigger manually via Prefect UI twice)
    - After second run: `SELECT model_version, rmse, is_champion FROM model_registry ORDER BY trained_at;`
    - Should show two rows — one champion (lower RMSE), one challenger
    - `docker exec -it nasdaq-pipeline ls /app/models/` should show: `champion.pkl`, `model_v1.pkl`, `model_v2.pkl`, `metrics_model_v1.json`, `metrics_model_v2.json`



----
**Task 4.0: Streamlit Dashboard** **Owner:** `[Nifra]` | **Start:** `2026-04-23` | **Status:** *In Progress*

---
**Task 5.0: Logging & Monitoring** **Owner:** `[Nifra]` | **Start:** `2026-04-` | **Status:** *In Progress*

---
**Task 6.0: Pipeline Orchestration** **Owner:** `[Nifra]` | **Start:** `2026-04-23` | **Status:** *In Progress*


---
**Task 7.0: Project Documentation** **Owner:** `[]` | **Start:** `2026-04-` | **Status:** *Pending*
* maximum 3 pages
* Team Details: Roll numbers and 1-2 line contributions of each member
* Project Description: Title, goal, dataset, and domain/theme (1-2 paragraphs)
* Architecture Diagram: Use draw.io or similar
* Schema Diagram: Show data models and relationships
* Pipeline Explanation: Brief overview of each stage with tool justification
* Deployment Link: Link to deployed demo/interface (if publicly accessible)
* Repository: GitHub link to your repo/folder
* AI Usage Disclosure: Clearly specify use of AI in documentation (mandatory for visibility and judging)
* AI Usage Declaration Format1 
   AI Usage Declaration2 
   - Tool : ChatGPT3 
   - Used for : Debugging syntax errors in FastAPI routes , understanding Airflow concepts4 
   - Extent : No code generation , only debugging assistance



---
**Task 8.0: Demo (Video File)** **Owner:** `[]` | **Start:** `2026-04-` | **Status:** *Pending*
* *Duration: 1-2 minutes (strict maximum)
* Content: Must show:
* – Pipeline execution (triggering the pipeline and observing it run)
* – System output (API calls with responses OR dashboard interactions)
* – Architecture explanation (walk through your design)
* – Code walkthrough (brief explanation of key components)
* Format: Voice over recommended