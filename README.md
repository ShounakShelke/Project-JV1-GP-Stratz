# GP-Stratz: Motorsport Strategy Environment
**An OpenEnv Hackathon Submission**

## Problem Statement
In elite motorsport, victory isn't just about raw speed; it's about making critical strategic decisions under pressure. A human race strategist must constantly analyze tyre degradation, shrinking competitor gaps, and unpredictable weather changes. A single-lap delay in switching to wet-weather tyres or pitting for fresh slicks can cost 30+ seconds or result in a high-speed crash (DNF). 

**GP-Stratz** provides a deterministic, lightweight simulation of this high-stakes decision-making process. The goal is to evaluate an AI agent's ability to act as a race strategist, minimizing total race time over an episodic trajectory without relying on complex physical telemetry.

---

## Environment Overview
GP-Stratz is built on the `OpenEnv` framework principles. It simulates a sequential multi-lap race where every action heavily influences the next state.
*   **Time step:** 1 Step = 1 Lap.
*   **Determinism:** Given a starting scenario seed, the environment returns identical states for identical agent actions.
*   **Goal:** Reach the `done` state (completing the required number of laps) with the maximum cumulative reward (which translates to the shortest race time).

---

## State Space
The environment emits a simple but dense state vector (Max 5 variables) at the start of every lap:

| Variable | Range | Description | Why it matters |
| :--- | :--- | :--- | :--- |
| `lap_number` | `0` to `max_laps` | The current position in the race. | Late-race decisions differ from early-race strategy. |
| `tyre_wear` | `0` to `100` | Percentage of grip degradation. | >85% wear is dangerous. 100% is a DNF (crash). |
| `weather` | `0` (Clear), `1` (Soon), `2` (Rain) | Impending or current rain. | Wet conditions require Wet tyres. |
| `gap_to_car` | `float` (seconds) | Time gap to the nearest rival. | Smaller gaps require "Push" or "Undercut" tactics. |
| `tyre_type` | `0` (Slicks), `1` (Wets)| Current equipment fitted. | Matching tyre type to weather is critical for base pace. |

---

## Action Space
The agent chooses one of 5 discrete actions per step:

| ID | Action | Effect | Ideal Use Case |
| :--- | :--- | :--- | :--- |
| **0** | **PIT** | +20s penalty. Resets wear to 0. | When tyres are critical (>85 wear). |
| **1** | **STAY OUT** | Normal base lap time (e.g. 90s). +wear. | Standard racing state. Tyres are healthy. |
| **2** | **CONSERVE**| +2s to lap time. Wear increases by 50% less. | Stretching a tyre stint to avoid an extra pit stop. |
| **3** | **PUSH** | -2s from lap time. Wear increases by 2x. | Chasing a close rival to attempt an overtake. |
| **4** | **SWAP STRAT**| +20s pit stop. Changes Slicks <-> Wets. | Mandatory when weather jumps between Clear and Rain. |

---

## Reward Function (Trajectory Based)
The reward system evaluates the *trajectory* of the race, punishing poor strategy and rewarding efficiency. It is **not** binary.

**Reward = `Target_Lap_Time` - `Actual_Lap_Time`**
*(Higher reward = faster lap)*

**Components that affect `Actual_Lap_Time`:**
* **`+0.5` (Correct Decision Bonus):** e.g., Pushing successfully, or Swapping when Rain hits.
* **`+0.2` (Tyre Management):** Conserving when needed.
* **`-20.0` (Pit Stop):** Necessary evil, but costs time.
* **`-5.0` (Wrong Tyres):** Driving slicks in the rain.
* **`-500.0` (DNF Penalty):** Allowing `tyre_wear` to hit `100`. Terminates episode negatively.

---

## Task Descriptions (The Dataset)

### Task 1 (Easy): Pit Timing Fundamentals
*   **Focus:** Single-axis decision-making. 
*   **Variables:** Only considers `lap_number` and `tyre_wear`. Weather is always clear.
*   **Goal:** Teach the agent to pit before wear reaches 100, but not so early that they waste time.
*   **Example State:** `{wear: 88, lap: 15, weather: clear}` -> **Action 0 (Pit)**.

### Task 2 (Medium): Multi-Factor Strategy
*   **Focus:** Complex trade-offs, trajectory planning.
*   **Variables:** Introduces dynamic `weather` and `gap_to_car`.
*   **Goal:** Optimize decisions across laps. (e.g. Risking high tyre wear to survive until the rain arrives to save a double pit-stop).
*   **Example State:** `{wear: 82, lap: 12, gap: 20.0, weather: rain_soon}` -> **Action 2 (Conserve)**.

---

## File Structure
```text
project-jv1/
├── env/
│   └── race_env.py      # Core OpenEnv class implementation (reset, step).
├── data/
│   └── generate_data.py # Script generating the deterministic dataset.
│   └── scenarios.json   # (Created) Easy & Medium scenario state/action pairs.
├── grader/
│   └── evaluate.py      # Runner that pits an agent against the dataset.
├── README.md            # Project documentation.
├── requirements.txt     # Python dependencies.
├── app.py               # (Optional) Interactive CLI runner.
└── Dockerfile           # Standardized container logic for OpenEnv platform.
```

---

## To Run & Test

**1. Setup Environment**
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
```

**2. Generate Dataset**
*The dataset is deterministic and generated mathematically based on our rules engine.*
```bash
python data/generate_data.py
```

**3. Run the Environment (Manual Test)**
```bash
python app.py
```

**4. Evaluate Agent against Grader**
```bash
python grader/evaluate.py
```
