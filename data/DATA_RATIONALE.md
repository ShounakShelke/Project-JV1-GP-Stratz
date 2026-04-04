# GP-Stratz: Data Generation & Strategic Rules Logic

This project includes `generate_data.py` to ensure complete **transparency** and **reproducibility** in how the race strategy scenarios were created. This document explains the internal logic so that judges and researchers can understand the decision-making rules used to label the "Optimal Actions."

---

## Why this file exists

1.  **Transparency**: Judges can see exactly how "Optimal" is defined. There is no "black box" logic.
2.  **Scalability**: Adding **Task 3 (Hard Mode)** or refining existing scenarios is as simple as adding a rule to the script rather than manually editing a 700+ line JSON file.
3.  **Standard Practice**: In OpenEnv research, providing the **Scenario Generator** is a requirement for a high-quality, reproducible submission.

---

## The "Golden Rules" of GP-Stratz
The generator script follows a strict hierarchy of **9 Strategic Rules**. When a scenario is generated, these rules are checked in order from highest priority to lowest:

### 1. Environmental Priority (Highest)
*   **R1: Weather == Rain** → **Action: SWAP (4)**
    *   *Driving on slicks in the rain is a safety failure. This rule overrides all others.*

### 2. Safety & Reliability
*   **R2: Tyre Wear >= 86%** → **Action: PIT (0)**
    *   *Tyres are critical. To avoid DNF, we must pit immediately.*

### 3. Tactical Efficiency (Impending Rain)
*   **R3: Rain Coming & Wear >= 70%** → **Action: CONSERVE (2)**
    *   *Don't pit now if it's about to rain. Conserve tyres to reach the "wet window" and save an extra stop.*
*   **R4: Rain Coming & Wear < 70%** → **Action: STAY OUT (1)**
    *   *Tyres are healthy enough; just hold position until the weather flips.*

### 4. Pace Management (Clear Weather)
*   **R5: Wear 60–85% & Gap >= 5.0s** → **Action: CONSERVE (2)**
    *   *You have a safe gap behind. Protect your tyres to extend the stint.*
*   **R6: Wear < 50% & Gap < 2.0s** → **Action: PUSH (3)**
    *   *Fresh tyres + Close rival = Overtake attempt (The Undercut).*

### 5. Standard Operation (Lowest)
*   **R7/R8/R9: Default Case** → **Action: STAY OUT (1)**
    *   *If we are not in danger and there is no clear attacking opportunity, maintain pace.*

---

## Output Formats
The script automatically exports the logic into three usable formats in the `data/` folder:
*   `scenarios.json`: Direct input for the **OpenEnv Grader**.
*   `scenarios.csv`: For quick visual analysis in tables.
*   `scenarios.xlsx`: For spreadsheet-based strategy review.

---
**Note**: The Environment Reward System (`env/race_env.py`) and the Evaluator (`grader/evaluate.py`) are strictly aligned with these rules, ensuring that a **PASS** in the evaluation always matches the highest mathematical reward.
