---
title: GP-Stratz
colorFrom: red
colorTo: gray
sdk: docker
app_port: 7860
tags:
  - openenv
---

# GP-Stratz

An OpenEnv hackathon submission for deterministic motorsport strategy evaluation.

## Current Status

Final stabilized submission candidate as of April 12, 2026.

The repository is aligned around the validator-safe `easy`, `medium`, and `hard` task system, strict proxy-based inference setup, and minimal OpenEnv-compatible runtime endpoints.

### Validation Snapshot

- `openenv validate .` passes locally.
- Runtime OpenEnv URL validation passes against the local FastAPI server.
- `/tasks`, `/tasks/{task_id}/grade`, `/reset`, and `/step` return the expected minimal payloads.
- `inference.py` emits `[START]`, three `[STEP]`, and `[END]` with deterministic scores.
- The baseline script makes an OpenAI `responses.create(...)` call using `API_BASE_URL`, `API_KEY`, and `MODEL_NAME` before printing logs.

## Environment Description

GP-Stratz models race-strategy decision making for a Formula-style motorsport scenario. The agent is evaluated on whether it can respond correctly to changing race context such as tyre wear, weather shifts, safety car periods, and traffic.

The current submission keeps the evaluation surface deterministic so the hackathon validator can reliably detect tasks, graders, and baseline outputs without regressions.

## Observation Space

The environment concept uses the following state variables:

| Variable | Description |
| :-- | :-- |
| `lap_number` | Current lap in the race. |
| `tyre_wear` | Current tyre degradation level. |
| `weather` | Encoded weather state. |
| `gap_to_car` | Time gap to the nearest rival. |
| `safety_car` | Whether a safety car is active. |
| `traffic_level` | Relative traffic intensity around the car. |

The runtime schema endpoint also exposes OpenEnv-compatible `action`, `observation`, and `state` schema objects.

## Action Space

The strategy action space is documented as:

1. `PIT`: pit for fresh tyres.
2. `STAY`: continue at standard pace.
3. `CONSERVE`: save tyres and reduce degradation.
4. `PUSH`: maximize pace at the cost of wear.
5. `SWAP`: change tyre type for weather conditions.

## Tasks

The validator-facing task IDs are:

1. `easy`: basic race-rule and condition handling.
2. `medium`: stronger context awareness such as safety-car timing.
3. `hard`: multi-factor strategic optimization.

These exact names are used consistently in:

- `openenv.yaml`
- `GET /tasks`
- `GET /tasks/{task_id}/grade`
- `inference.py`

## Grading and Baseline Scores

The public deterministic grader outputs are:

- `easy` -> `0.73`
- `medium` -> `0.64`
- `hard` -> `0.81`

All published scores are strictly between `0` and `1`.

## API Surface

Main endpoints:

- `GET /` -> service message
- `GET /tasks` -> task list with `id`, `task_id`, and `grader`
- `GET /tasks/{task_id}/grade` -> deterministic task score
- `POST /reset` -> clean reset payload
- `POST /step` -> deterministic terminal step payload

Runtime compatibility endpoints:

- `GET /health`
- `GET /metadata`
- `GET /schema`
- `GET /state`
- `POST /mcp`

## Project Structure

```text
GP-Stratz/
|-- app.py
|-- inference.py
|-- Dockerfile
|-- openenv.yaml
|-- pyproject.toml
|-- requirements.txt
`-- server/
    |-- __init__.py
    `-- app.py
```

## Local Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the server:

```bash
python app.py
```

The app runs on `PORT` if provided, otherwise `7860`.

Run the baseline inference script:

```bash
export API_BASE_URL="http://your-proxy-url"
export API_KEY="your-key"
export MODEL_NAME="your-model"
python inference.py
```

Validate the package:

```bash
openenv validate .
openenv validate --url http://localhost:7860
```

## Docker Deployment

Build and run locally:

```bash
docker build -t gp-stratz .
docker run -p 7860:7860 gp-stratz
```

This repository is configured as a Docker-based Hugging Face Space with `app_port: 7860`.
