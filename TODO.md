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

**Task 2.0:** Strengthen `prices` Cleaning Rules  
**Owner:** `[]` | **Start:** `2024-05-23` | **Status:**  *Pending*


---
