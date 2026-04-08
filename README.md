---
title: GP-Stratz
emoji: 🏎️
colorFrom: red
colorTo: gray
sdk: docker
app_port: 8000
---

# GP-Stratz: Motorsport Strategy Environment
**An OpenEnv Hackathon Submission**

## Current Status
**Phase 2 / Pre-Validation Checks Passed (April 2026)**
The submission has been heavily optimized and is now fully immune to previous validation pipeline fails. Recent patches include:
* **Docker/HF Spaces Health Compliance:** Explicitly routing and bounding HuggingFace container port (`8000`) perfectly in `Dockerfile` to match `openenv.yaml`, fixing any 30-minute boot timeouts.
* **OpenEnv spec compliance:** Explicit separation of graded tasks (`easy`, `medium`, `hard`) inside `openenv.yaml` that trigger dedicated command-line endpoint metrics.
* **Secure Score Bounds:** Overhauled evaluation and bounding logic in `grader/evaluate.py` to securely guarantee all scores fall exclusively within `(0.001` and `0.999)`, satisfying strictly `(0, 1)`.
* **Strict Inference STD-Out:** Fully adheres to OpenEnv's new parsing rules by avoiding unstructured JSON dumps inside inference strings, matching EXACTLY to `<key>=<value>` pairs on a single line (`[START]`, `[STEP]`, `[END]`).

## What GP-Stratz Does
**GP-Stratz** provides a deterministic, lightweight simulation of a high-stakes motorsport race. It asks an AI agent to act as a race strategist, minimizing total race time over an episodic trajectory by making lap-by-lap decisions on pitting, tyre conservation, pushing, and reacting to changing weather conditions.

## Why It Matters
In elite motorsport, victory isn't just about raw speed; it's about making critical strategic decisions under pressure. A human race strategist must constantly analyze tyre degradation, shrinking competitor gaps, and unpredictable weather changes. A single-lap delay in switching to wet-weather tyres or pitting for fresh slicks can cost 30+ seconds or result in a high-speed crash (DNF). This environment tests an LLM's capacity to emulate these high-pressure, deterministic strategic rules in a zero-shot or few-shot manner.

## How the Environment Works
The environment accepts a state input vector and returns a reward based on a carefully tuned physical model of a race. It maintains a consistent sequence logic over a maximum of 30 laps, tracking tyre wear, gaps between cars, traffic, and weather.

### The State Variables
The environment emits a feature-rich state vector at the start of every lap:

| Variable | Range | Description |
| :--- | :--- | :--- |
| `lap_number` | `1-30` | The current lap number. |
| `tyre_wear` | `0-100` | Percentage of grip wear. >86% is critical. 100% results in DNF. |
| `weather` | `0, 1, 2` | 0: Clear, 1: Rain Soon, 2: Rain. |
| `gap_to_car` | `float` | Gap to the nearest rival. |
| `safety_car` | `bool` | True / False. Pit stops under SC cost less time. |
| `traffic_level`| `0, 1, 2` | 0: Low, 1: Medium, 2: High. High traffic blocks pushing. |
| `tyre_deg_rate`| `float` | Base scalar for tyre wear. |
| `tyre_type`  | `0, 1` | 0: Slicks, 1: Wets. |

### The Action Space
The agent can choose from 5 discrete actions:
*   **0: PIT**: Resets wear to 0. Optimal when wear is critical or under Safety Car.
*   **1: STAY**: Maintain current pace.
*   **2: CONSERVE**: Reduces tyre wear but slows pace. Ideal for extending a stint.
*   **3: PUSH**: Increases pace but destroys tyres faster. Good for overtaking if gap is small.
*   **4: SWAP**: Mandatory pit stop to change tyres for rain.

## Reward Design (Trajectory-Based)
The reward engine is normalized to `[-2.0, +2.0]` with four key components:
1.  **Correctness (+1.2 / -1.2)**: The dominant term based on golden-rule correctness.
2.  **Forward Bonus (+0.4)**: Rewarded for "High-IQ" strategic moves (e.g., Pitting under Safety Car, extending a stint just before rain).
3.  **Sequence Consistency (+0.3)**: Reward for maintaining strategy over 3 consecutive laps.
4.  **Inconsistency Penalty (-0.3)**: Punishes erratic "flip-flopping" between PUSH and CONSERVE.

## Tasks and Grading System

GP-Stratz features 3 explicit tasks for evaluation, each with its own dedicated grading logic:

*   **Task 1 (Easy)**: Single-step optimal decisions (e.g., matching tyre type to weather, pitting when critically worn). Validates the agent's fundamental awareness of race rules.
*   **Task 2 (Medium)**: Contextual decisions (e.g., holding out for expected rain, capitalizing on Safety Cars, managing traffic). Validates the agent's ability to handle multi-factor environmental variables.
*   **Task 3 (Hard)**: Multi-step sequential strategies. The agent must successfully navigate a 3-5 lap continuous sequence, such as a managed undercut attempt without burning out the tyres.

### Grading Logic

The system uses a strict deterministic grading pipeline:
1.  **Independent Scoring**: Each task (Easy, Medium, Hard) is evaluated independently against its respective Scenario subsets in the dataset.
2.  **Normalization**: Every individual task score is strictly normalized to be between `(0, 1)` using the following guarantee:
    *   If `score >= 1.0`, it is capped at `0.999`.
    *   If `score <= 0.0`, it is floored at `0.001`.
    *   This ensures no boundary values (0.0 or 1.0) interfere with the validator.
3.  **Final Aggregation**: The final overall score is calculated as the simple average of the three task scores:
    `final_score = (easy_score + medium_score + hard_score) / 3`
    The final score is also normalized to stay within the strict `(0, 1)` range.

### Sample Output Format

The `inference.py` script and the `/benchmark` endpoint return a structured JSON block in the `[END]` tag:

```json
[END] {
  "score": 0.82,
  "tasks": {
    "easy": 0.84,
    "medium": 0.80,
    "hard": 0.76
  }
}
```

## File Structure
```text
GP-Stratz/
  env/
    race_env.py             # OpenAI Gym-style Base Environment
  data/
    generate_data.py        # Scenario & Dataset Generator
    dataset.json            # Generated Truth Dataset
  grader/
    evaluate.py             # Local Grader and Baseline Logic
  others/
    notes/                  # Old design docs, logic rationale
    temp/                   # Legacy dataset formats
  app.py                    # OpenEnv Validation Web Server
  inference.py              # Main LLM Inference Script benchmark wrapper
  openenv.yaml              # OpenEnv Manifest
  requirements.txt          # Python Dependencies
  Dockerfile                # Validation Container config
```

## How to Run Locally
1. Keep the dependencies ready:
```bash
pip install -r requirements.txt
```
2. Generate the dataset if needed:
```bash
python data/generate_data.py
```
3. Run the Grader manually:
```bash
python grader/evaluate.py
```

## How to Test Inference
To run the LLM baseline against the environment:
```bash
# Provide variables
export API_BASE_URL="https://api.openai.com/v1"  # Or Groq/HF etc
export MODEL_NAME="gpt-4o-mini"
export HF_TOKEN="your_token_here"

python inference.py
```

## How to Validate with OpenEnv
```bash
# 1. Install OpenEnv Core
pip install openenv-core

# 2. Run Local FastApi Server (Optional check)
python app.py

# 3. Test Full OpenEnv Compliance Validation
openenv validate
```

## How to Build Docker
```bash
docker build -t gp-stratz:latest .
docker run -p 8000:8000 gp-stratz:latest
```
The Docker container exposes `app.py` directly, matching OpenEnv requirements.
