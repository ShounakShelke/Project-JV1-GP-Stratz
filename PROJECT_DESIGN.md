# Project JV1 - "GP Stratz"
## Complete Design Blueprint (OpenEnv Hackathon)

---

### 1. FINAL PROBLEM STATEMENT
**The Problem:** In elite motorsport, races are won or lost on the pit wall. Human strategists must manage tyre degradation, unpredictable weather, and competitor gaps under extreme pressure. A 1-lap delay in pitting for rain tyres can cost 30+ seconds.
**Why it matters:** Strategic errors lead to loss of points and revenue. 
**Target Users:** Race engineering teams, automated strategy systems, and AI researchers testing tactical decision-making in constrained environments.

---

### 2. PROJECT OBJECTIVE
The environment aims to evaluate an agent's ability to minimize **Cumulative Race Time** over a fixed number of laps.
*   **Success:** Achieving the lowest total time (base time + penalties) while maintaining terminal safety (tyre wear < 100%).

---

### 3. SCOPE DEFINITION

| **INCLUDE** | **EXCLUDE** |
| :--- | :--- |
| Strategic pit-stop timing | Real-time physics/aerodynamics |
| Tyre wear & compound management | Multi-car collision physics |
| Dynamic weather transitions (Dry/Rain) | Model training logic (Environment only) |
| Deterministic time-based rewards | Frontend Visuals/Animations |

---

### 4. STATE SPACE DESIGN (State Vector: Length 5)

| Variable | Type | Range | Purpose |
| :--- | :--- | :--- | :--- |
| `lap_number` | `int` | `0` to `20` | Tracks race progression. |
| `tyre_wear` | `float` | `0.0` - `100.0` | Reflects grip loss and burst risk. |
| `weather` | `int` | `0` (Dry), `1` (Wet) | Global track condition. |
| `gap_to_ahead`| `float` | `0.0` - `10.0s` | Proximity to rival for overcut/undercut. |
| `tyre_type` | `int` | `0` (Slicks), `1` (Wets) | Current equipment on the vehicle. |

---

### 5. ACTION SPACE DESIGN (Discrete: 0-4)

| ID | Action | Result | Ideal Use Case |
| :--- | :--- | :--- | :--- |
| **0** | **PIT** | 20s Stop + 0% Wear | When wear > 80% or weather changes. |
| **1** | **STAY OUT** | Normal Pace | Default action when tyres feel "good". |
| **2** | **CONSERVE**| -2s Pace / -50% Wear | Managing a long stint to avoid a pit stop. |
| **3** | **PUSH** | +2s Pace / +2x Wear | Chasing the car ahead or "Quali" laps. |
| **4** | **SWAP** | Pit + Tyre Change | Mandatory when weather flips (Dry <-> Wet). |

---

### 6. EPISODE DESIGN
*   **Duration:** 15 Laps (approx. 5 minutes real-time simulation).
*   **Steps:** 1 Lap = 1 Step.
*   **Termination:** 
    1. Race Finish (Lap 15).
    2. Tyre Failure (Wear reached 100%).
    3. Severe Off-track (Optional).

---

### 7. INITIAL REWARD DESIGN (Optimization-based)
The agent seeks to maximize a cumulative reward (minimize time):
*   **Lap Reward:** `100 - Current Lap Time`.
*   **Pit Penalty:** `-20.0` reward points per stop.
*   **DNF Penalty:** `-500.0` points (Automatic failure).
*   **Partial Success:** Balancing wear to reach the end without an extra stop gains a "Longevity Bonus".

---

### 8. ENVIRONMENT FLOW (The Loop)
`State (L1, W10, D0, G2, T0)` → **Agent** → `Action (PIT)` → **Env** → `Reward (-20.0)` → `Next State (L2, W0, D0, G5, T0)`

1. **State:** Provided at start of Lap.
2. **Action:** Agent decision.
3. **Transition:** Wear increases, weather shifts (stochastic or scripted), time is calculated.
4. **Reward:** Lap duration subtracted from total score.

---

### 9. SIMPLICITY CONSTRAINTS
*   **Determinism:** Given a scenario ID, the environment must produce identical outputs for the same actions.
*   **No Randomness:** Grading is done on fixed weather patterns (e.g., "Rain on Lap 5").
*   **Max 5 Vars / 5 Actions:** Simplified enough for a solo developer to implement in 24 hours.

---

### 10. OPENENV DESIGN BLUEPRINT
```python
class MotorsportEnv:
    def reset(self, scenario_id=0):
        # Initialize variables
        return initial_state

    def step(self, action):
        # 1. Update wear/weather
        # 2. Calculate lap time
        # 3. Calculate reward
        return state, reward, done, info

    def state(self):
        # Current observation
        return state_array
```

---

### 11. PROJECT STRUCTURE
```text
project/
├── env/                # Core environment physics
├── scenarios/          # JSON files defining weather patterns
├── grader/             # Script to run submission vs scenarios
├── app.py              # CLI for running the environment
├── Dockerfile          # For OpenEnv submission compliance
└── README.md           # Instructions
```

---

### 12. SUCCESS CRITERIA
*   **Logical Consistency:** "Pushing" faster results in shorter lap time but higher wear.
*   **Reward Sensitivity:** Better strategy = significantly higher reward.
*   **Reproducibility:** Anyone can run the same agent/seed and get the same result.

---

### 13. COMMON PITFALLS
*   **Too much realism:** Calculating exact G-forces (Not needed).
*   **Infinite loops:** Not terminating on tyre failure.
*   **Vague Rewards:** Only rewarding at the finish line (makes training hard).
