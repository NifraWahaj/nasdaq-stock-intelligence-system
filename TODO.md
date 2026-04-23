# TODO

**Task 1.0:** Strengthen `prices` Cleaning Rules  
**Owner:** `[]` | **Start:** `2024-05-23` | **Status:**  *Pending*

Upgrade the ingestion pipeline with strict validation before `prices` insertion. Maintain `raw_prices` as an immutable audit log.
*   **Target File:** `ingestion/fetcher.py`
*   **Target Function:** `clean_ticker(df)`
*   **Current State:** Only removes NaNs and `close <= 0`.

- [ ] **1.1 Null Handling:** Drop row if `open`, `high`, `low`, `close`, or `volume` is NULL.
- [ ] **1.2 Price Consistency:** Drop if `high < low`, `high < open/close`, or `low > open/close`.
- [ ] **1.3 Positive Constraints:** All OHLCV values must be `> 0`.
- [ ] **1.4 Outlier Filter:** Drop rows where `abs(daily_return) > 0.5`.
- [ ] **1.5 Deduplication:** Strict uniqueness on `(date, symbol)`.
- [ ] **1.6 Open Discovery:** *Add additional data constraints as identified during implementation.*
- [ ] **1.7 Audit Integrity:** Ensure `raw_prices` is untouched.
- [ ] 1.8 Volume sanity: Drop rows where volume < 100

---

**Task 2.0: Expand Great Expectations Suite** **Owner:** `[]` | **Start:** `2026-04-` | **Status:** *Pending*

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
**Task 3.0: ML Model** **Owner:** `[]` | **Start:** `2026-04-` | **Status:** *Pending*
