# GP-Stratz: Motorsport Strategy Environment
**An OpenEnv Hackathon Submission**

## Problem Statement
In elite motorsport, victory isn't just about raw speed; it's about making critical strategic decisions under pressure. A human race strategist must constantly analyze tyre degradation, shrinking competitor gaps, and unpredictable weather changes. A single-lap delay in switching to wet-weather tyres or pitting for fresh slicks can cost 30+ seconds or result in a high-speed crash (DNF). 

**GP-Stratz** provides a deterministic, lightweight simulation of this high-stakes decision-making process. The goal is to evaluate an AI agent's ability to act as a race strategist, minimizing total race time over an episodic trajectory without relying on complex physical telemetry.

---

## Project Status: **V4 Production Ready**
*   **Accuracy**: 100.0% (37/37 Scenarios correctly identified by Baseline Agent).
*   **Normalized Score**: 0.848 (Scale 0.0 - 1.0).
*   **Tasks**: Task 1 (Easy), Task 2 (Medium), Task 3 (Hard) fully implemented.
*   **Reward Alignment**: Verified ([OK] PASS rewards > FAIL rewards).

---

## Environment Variables (State Space)
The environment emits a feature-rich state vector (6 variables) at the start of every lap:

| Variable | Range | Description | Why it matters |
| :--- | :--- | :--- | :--- |
| `lap_number` | `1-30` | The current lap. | Late-race decisions differ from early-race strategy. |
| `tyre_wear` | `0-100` | Percentage of grip wear. | >86% is critical. 100% results in DNF (Crash). |
| `weather` | `0, 1, 2` | Clear, Soon, Rain. | Matching tyre type to weather is critical for pace. |
| `gap_to_car` | `float` | Gap to nearest rival. | Smaller gaps require "Push" or "Undercut" tactics. |
| `safety_car` | `bool` | True / False. | **Task 3:** Reduces pit stop time loss by 50% (10s vs 20s). |
| `traffic_level`| `0, 1, 2` | Low, Medium, High. | **Task 3:** High traffic blocks "Push" effectiveness. |

---

## Action Space
*   **0: PIT**: 20s loss (10s if SC). Resets wear to 0.
*   **1: STAY OUT**: Normal base lap time (e.g., 90s).
*   **2: CONSERVE**: +2s lap time penalty. Reduces wear by 50%.
*   **3: PUSH**: -2s lap time bonus. Increases wear by 1.8x.
*   **4: SWAP STRAT**: +20s pit stop. Mandatory Slicks ↔ Wets.

---

## Reward Function (Trajectory Based)
The V4 reward engine is normalized to `[-2.0, +2.0]` with four key components:
1.  **Correctness (+1.2 / -1.2)**: The dominant term based on scenario labels.
2.  **Forward Bonus (+0.4)**: Rewarded for "High-IQ" strategic moves (e.g., Pitting under Safety Car).
3.  **Sequence Consistency (+0.3)**: Reward for maintaining strategy over 3 consecutive laps.
4.  **Inconsistency Penalty (-0.3)**: Punishes erratic "flip-flopping" between PUSH and CONSERVE.

---

## Run Guide

### 1. Setup Environment
```bash
python -m venv venv
source venv/Scripts/activate  # Windows
pip install -r requirements.txt
```

### 2. Generate Deterministic Dataset
This script creates `scenarios.json` using the **10 Strategic Golden Rules**.
```bash
python data/generate_data.py
```

### 3. Evaluate Agent against Grader
Runs the baseline agent through Easy, Medium, and Hard (Multi-step) scenarios.
```bash
python grader/evaluate.py
```

### 4. Interactive Simulation (Manual Mode)
Puts YOU in the strategist's seat to test the physics engine manually. (WIP)
```bash
python app.py
```

---

## File Structure
*   `env/race_env.py`: The simulation engine & physics.
*   `data/generate_data.py`: The source-of-truth for scenario logic.
*   `grader/evaluate.py`: The evaluation pipeline & baseline agent.
*   `data/scenarios.json`: The final dataset (Task 1, 2, and 3).
*   `DEMO_GUIDE.md`: Detailed walk-through of showcase scenarios.
*   `DATA_RATIONALE.md`: Explanation of the 10 Golden Rules for judges.

---
**Submission for OpenEnv Hackathon | Powered by Scaler, Meta, PyTorch, & Hugging Face.**
