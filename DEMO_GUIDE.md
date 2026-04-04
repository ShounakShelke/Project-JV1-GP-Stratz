# GP-Stratz: Showcase & Demo Guide

This guide explains how to demonstrate the **GP-Stratz** environment. It covers the logic behind the simulation and how to interpret the agent's performance during a demo.

## Demo Flow Overview

A typical GP-Stratz session follows this cycle:
1. **Scenario Load**: The environment is seeded with a specific race context (Lap, Wear, Weather, etc.).
2. **Observation**: The Agent (or human) receives the current state.
3. **Strategic Choice**: An action (0-4) is selected.
4. **Environment Update**: The environment computes the outcome:
   - **Physics**: Tyre wear increases (or resets if Pitting).
   - **Strategy**: Correctness is checked against the "Golden Rules."
   - **Tactics**: Safety Car and Traffic conditional modifiers are applied.
5. **Reward Feedback**: A normalized reward `[-2.0, +2.0]` is returned, clearly separating good strategy from poor choices.

---

## Key Scenarios to Showcase

### 1. The "Cheap Pit" (Safety Car Advantage)
*   **Context**: Safety Car is out. Tyre wear is moderate (60%).
*   **The Logic**: Pitting under a Safety Car costs **10 seconds** instead of the usual **20 seconds**.
*   **Optimal Action**: `0 (PIT)`.
*   **Reward**: Higher than a normal pit stop due to the `forward_bonus` (Strategic efficiency).

### 2. High Traffic Stalemate
*   **Context**: Traffic Level is "High". Gap to the car ahead is 0.5s.
*   **The Logic**: In a DRS-train or heavy traffic, "Pushing" only destroys tyres without gaining position.
*   **Optimal Action**: `2 (CONSERVE)`.
*   **Reward**: Positive for preserving the tyre life for a "Clean Air" window later.

### 3. The Rain Crossover
*   **Context**: Weather is "Rain Soon". Tyre wear is 75% (Critical-ish).
*   **The Logic**: Pitting now for slicks would be a disaster because you'd have to pit again in 2 laps for Wets.
*   **Optimal Action**: `2 (CONSERVE)` or `1 (STAY)`.
*   **Success**: When the weather flips to "Rain", the agent immediately selects `4 (SWAP)`.

---

## Understanding the Output

When running `grader/evaluate.py`, you will see:

| Output Element | Meaning |
| :--- | :--- |
| **PASS** | Agent chose the mathematically optimal action. |
| **Reward ~ +1.2** | Standard correct decision. |
| **Reward > +1.4** | Exceptional strategic move (e.g. SC Pit or Rain anticipation). |
| **Normalised Score** | Total Reward / Max Possible (Shows consistency over the full race). |

---

## Step-by-Step Execution

1. **Initialize**: `python data/generate_data.py` (Ensures latest rule-set is active).
2. **Evaluate**: `python grader/evaluate.py` (Watch the 100% accuracy streak).
3. **Analyze**: Check `data/scenarios.csv` to see the exact state variables that led to each decision.

---
**Verdict**: GP-Stratz proves that AI can handle complex, multi-step race strategy by prioritizing safety, efficiency, and environmental awareness.
