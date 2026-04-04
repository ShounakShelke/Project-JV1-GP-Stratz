# GP-Stratz: Motorsport Strategy Environment
**An OpenEnv Hackathon Submission**

## Problem Statement
In elite motorsport, victory isn't just about raw speed; it's about making critical strategic decisions under pressure. A human race strategist must constantly analyze tyre degradation, shrinking competitor gaps, and unpredictable weather changes. A single-lap delay in switching to wet-weather tyres or pitting for fresh slicks can cost 30+ seconds or result in a high-speed crash (DNF). 

**GP-Stratz** provides a deterministic, lightweight simulation of this high-stakes decision-making process. The goal is to evaluate an AI agent's ability to act as a race strategist, minimizing total race time over an episodic trajectory without relying on complex physical telemetry.

---

## Environment Overview
GP-Stratz is built on the `OpenEnv` framework principles. It simulates a sequential multi-lap race where every action heavily influences the next state.
*   **Time step:** 1 Step = 1 Lap.
*   **Determinism:** 100% deterministic. Given a starting scenario seed, the environment returns identical states for identical actions.
*   **Tasks:** Supports three difficulty tiers (Easy, Medium, Hard).

---

## State Space
The environment emits a feature-rich state vector at the start of every lap:

| Variable | Range | Description | Why it matters |
| :--- | :--- | :--- | :--- |
| `lap_number` | `1-30` | Current lap of the race. | Late-race decisions differ from early-race strategy. |
| `tyre_wear` | `0-100` | Percentage of degradation. | >85% is critical. 100% results in DNF. |
| `weather` | `0, 1, 2` | Clear, Soon, Rain. | Matching tyre type to weather is critical for pace. |
| `gap_to_car` | `float` | Time gap to nearest rival. | Smaller gaps require "Push" or "Undercut" tactics. |
| `safety_car` | `bool` | True/False. | **New (Task 3):** Reduces pit stop time loss by 50%. |
| `traffic_level`| `0, 1, 2` | Low, Medium, High. | **New (Task 3):** High traffic blocks "Push" effectiveness. |
| `tyre_deg_rate`| `0.8-1.5`| Degradation multiplier. | **New (Task 3):** Simulates varying track abrasiveness. |

---

## Action Space
0 = **PIT** (20s loss, 0% wear) | 1 = **STAY OUT** | 2 = **CONSERVE** (-wear) | 3 = **PUSH** (+wear, -time) | 4 = **SWAP** (Changes compound)

---

## Reward Function (V3: Sequence Based)
GP-Stratz uses a **Trajectory-Based Reward** system normalized to `[-2.0, +2.0]` per step.

*   **Correctness (+1.0 / -1.0):** Dominant term based on scenario labels.
*   **Strategy Bonus (+0.3 to +0.5):** Rewarded for specific high-IQ moves (e.g., Pitting under Safety Car, Conserving to wait for Rain).
*   **Sequence Consistency (-0.3):** Penalty for erratic flipping between PUSH and CONSERVE in consecutive laps.
*   **DNF Penalty (-2.0):** Immediate penalty if wear hits 100.

---

## Task Descriptions

### Task 1 (Easy): Pit Timing
Basic threshold detection. Pit when wear is critical.

### Task 2 (Medium): Multi-Factor Strategy
Incorporates weather and gaps. Identifying the "crossover" point for rain.

### Task 3 (Hard): Multi-Step Strategic Simulation
**Sequence-based logic.** Agent must navigate 3-5 lap windows containing Safety Cars and Traffic stalemates. Decisions in Lap 1 deeply affect the viability of the stint in Lap 5.

---

## File Structure
```text
project/
├── env/                # RaceEnvironment engine
├── data/               # Scenario generation & JSON datasets
├── grader/             # Automated sequence-based evaluator
├── app.py              # Manual testing CLI
└── Dockerfile          # OpenEnv compliance
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
```bash
python data/generate_data.py
```

**3. Run Multi-Step Evaluation**
```bash
python grader/evaluate.py
```
