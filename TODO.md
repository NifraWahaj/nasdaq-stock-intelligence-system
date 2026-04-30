# TODO

**Task 1.0:** Ensure champion/challenger uses dual condition (RMSE + MAE)
**Owner:** `[Junaid]` | **Start:** `2026-05-` | **Status:**  *Pending*

File: ml/trainer.py
* Right now trainer.py promotes a challenger to champion if only RMSE improves. The spec requires both conditions to be true:
* - Condition 1: challenger RMSE < champion RMSE
* - Condition 2: challenger MAE ≤ champion MAE × 1.05 (5% tolerance for noise)

* If there is no existing champion, then the first model should always be promoted.
What to do
* dd a helper to fetch the current champion’s MAE (similar to how RMSE is fetched).
* Update the comparison logic in the training function:
* Pull both RMSE and MAE of the current champion
* Compare:
* - RMSE must improve
* - MAE must be within a 5% tolerance
* Only promote if both pass
* Add clear logging for all outcomes:
* - promoted (both conditions passed)
* - rejected due to RMSE
* - rejected due to MAE worsening

How to verify
* Run the pipeline twice
* Check model_registry table:
* Only one model should be marked as champion
* Check logs: You should clearly see whether the challenger was promoted or rejected and why

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
* AI Usage Declaration Format:
   AI Usage Declaration
   - Tool : ChatGPT
   - Used for : Debugging syntax errors in FastAPI routes , understanding Airflow concepts 
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