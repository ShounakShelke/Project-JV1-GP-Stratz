# GP-Stratz: Motorsport Strategy Environment

## 1. What this project does

GP-Stratz is a simulation-based AI environment where an agent acts as a race strategist.
The agent makes decisions such as when to pit, conserve tyres, or push performance based on race conditions.

The goal is to evaluate how well an AI system can make **real-world strategic decisions under dynamic conditions**.

---

## 2. Why this problem matters

In real motorsports (like Formula 1), strategy decisions:

* directly impact race outcomes
* involve uncertainty (weather, tyre wear, traffic)
* require balancing short-term vs long-term gain

Poor decisions can cost positions or entire races.

This environment simulates that complexity in a **controlled, testable way**.

---

## 3. What makes this project unique

* Not a toy problem — based on real-world race strategy
* Fully deterministic (no randomness)
* Multi-step decision-making (Task 3)
* Reward reflects real strategy impact
* Designed as an **evaluation system for AI agents**, not a training model

---

## 4. Environment Overview

The environment follows:

state → action → reward → next state

Each step simulates a race decision.

The agent interacts with the environment across multiple steps (laps).

---

## 5. State (Observation Space)

The agent observes:

* lap_number → current lap
* tyre_wear → tyre degradation (0–100)
* weather → clear / rain_soon / rain
* gap_to_car → distance to competitor
* safety_car → whether safety car is active
* traffic_level → race congestion
* tyre_degradation_rate → wear speed

---

## 6. Action Space

The agent can choose:

0 → pit
1 → stay out
2 → conserve tyres
3 → push hard
4 → change tyre strategy

Each action affects future race conditions.

---

## 7. Tasks

### Task 1 (Easy)

* Focus: basic pit timing
* Variables: lap, tyre wear
* Goal: learn simple decision boundaries

---

### Task 2 (Medium)

* Adds: weather, gap
* Goal: multi-factor decision-making

---

### Task 3 (Hard)

* Adds: safety car, traffic, degradation
* Multi-step strategy required
* Decisions impact future states

---

## 8. Reward Function

Reward is designed to reflect:

* correctness of decision
* tyre management efficiency
* lap time improvement
* long-term strategic benefit

Key properties:

* deterministic
* normalized (-2 to +2)
* aligned with correctness (PASS > FAIL)
* includes partial rewards

---

## 9. How the system works

1. Environment initializes state
2. Agent observes state
3. Agent selects action
4. Environment updates state
5. Reward is calculated
6. Process repeats until episode ends

Final score is computed from cumulative reward.

---

## 10. Evaluation Method

* Each scenario has an optimal action
* Agent decisions are compared against it
* Reward is accumulated
* Final score is normalized (0–1)

---

## 11. Why no ML model is used

This project focuses on:

* environment design
* decision evaluation
* reproducibility

The goal is not to train AI, but to **test AI behavior**.

---

## 12. Design principles followed

* simplicity over complexity
* deterministic logic
* real-world relevance
* clear reward alignment
* scalable difficulty

---

## 13. What makes this strong for the hackathon

* Unique real-world problem
* Clean environment design
* Multi-step decision logic
* Strong evaluation system
* Fully reproducible results

---

## 14. Final summary

GP-Stratz is a **real-world inspired decision-making environment** where an AI agent must think strategically over time.

It demonstrates:

* environment design
* reward engineering
* decision modeling

and aligns strongly with the hackathon’s evaluation criteria.
