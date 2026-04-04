import json
import pandas as pd
import os

# ═══════════════════════════════════════════════════════════════════
#  GP-Stratz Dataset Generator  v4  |  Hard-Mode Optimized
# ═══════════════════════════════════════════════════════════════════
#
#  10 RULES  —  mutually exclusive, priority-ordered.
#  This ruleset is duplicated exactly in:
#    - grader/evaluate.py  (agent)
#    - env/race_env.py     (physics thresholds)
#
#  R1:  weather == RAIN                          → SWAP   (4)
#  R2:  tyre_wear >= 86                          → PIT    (0)
#  R3:  safety_car == True  AND  wear >= 55      → PIT    (0)   ← cheap pit
#  R4:  safety_car == True  AND  wear <  55      → STAY   (1)   ← already fresh
#  R5:  weather == RAIN_SOON  AND  wear >= 70    → CONSERVE (2) ← survive for swap
#  R6:  weather == RAIN_SOON  AND  wear <  70    → STAY   (1)   ← hold position
#  R7:  traffic == HIGH  AND  gap <= 1.0         → CONSERVE (2) ← stalemate
#  R8:  weather == CLEAR  AND  60 <= wear <= 85
#         AND  gap >= 5.0                        → CONSERVE (2) ← stretch stint
#  R9:  weather == CLEAR  AND  wear < 50
#         AND  gap < 2.0  AND  traffic < 2      → PUSH   (3)   ← undercut
#  R10: (default)                                → STAY   (1)
#
# ═══════════════════════════════════════════════════════════════════

dataset = []

# ----------------------------------------------------------------
# TASK 1  —  EASY  (10 clear-weather wear-only scenarios)
# ----------------------------------------------------------------
# Rules in play: R2, R8, R9, R10
easy = [
    # STAY (R10) — low wear, safe gap
    {"wear":10, "lap":1,  "gap":5.0,  "act":1, "r":"R10: low wear, cruising"},
    {"wear":25, "lap":8,  "gap":12.0, "act":1, "r":"R10: healthy tyres"},
    {"wear":45, "lap":15, "gap":3.0,  "act":1, "r":"R10: moderate wear, large gap → stay"},
    {"wear":55, "lap":20, "gap":2.5,  "act":1, "r":"R10: wear 50-59, below conserve band"},
    # CONSERVE (R8) — wear 60-85 AND gap >= 5
    {"wear":62, "lap":18, "gap":8.0,  "act":2, "r":"R8: wear in 60-85, gap>=5, clear → conserve"},
    {"wear":75, "lap":25, "gap":7.0,  "act":2, "r":"R8: wear in 60-85, gap>=5, clear → conserve"},
    # PUSH (R9) — wear < 50, gap < 2, clear, low traffic
    {"wear":30, "lap":12, "gap":1.5,  "act":3, "r":"R9: fresh tyres + close rival → push"},
    {"wear":40, "lap":18, "gap":0.8,  "act":3, "r":"R9: good tyres + attack position → push"},
    # PIT (R2) — wear >= 86
    {"wear":88, "lap":20, "gap":4.0,  "act":0, "r":"R2: wear>=86, must pit"},
    {"wear":95, "lap":26, "gap":1.0,  "act":0, "r":"R2: wear>=86, critical, pit now"},
]
for d in easy:
    dataset.append({
        "state": {"lap_number":d["lap"],"tyre_wear":d["wear"],"weather":"clear","gap_to_car":d["gap"],"safety_car":False,"traffic_level":0},
        "optimal_action":d["act"], "difficulty":"easy", "metadata":{"reason":d["r"],"edge_case":False}
    })

# ----------------------------------------------------------------
# TASK 2  —  MEDIUM  (15 scenarios, weather + gap)
# ----------------------------------------------------------------
# Rules in play: R1-R3 not yet; R5-R10
medium = [
    # SWAP (R1) — rain active
    {"w":"rain",     "wear":20, "lap":10, "gap":5.0, "sc":False, "tr":0, "act":4, "r":"R1: rain, must swap"},
    {"w":"rain",     "wear":50, "lap":28, "gap":2.0, "sc":False, "tr":0, "act":4, "r":"R1: rain, mid-wear, swap"},
    {"w":"rain",     "wear":90, "lap":8,  "gap":5.0, "sc":False, "tr":0, "act":4, "r":"R1: rain + high wear, swap urgently"},
    # PIT (R2) — wear >= 86, clear
    {"w":"clear",    "wear":88, "lap":14, "gap":5.0, "sc":False, "tr":0, "act":0, "r":"R2: wear>=86, pit"},
    {"w":"clear",    "wear":92, "lap":29, "gap":1.0, "sc":False, "tr":0, "act":0, "r":"R2: wear>=86, last lap, pit or DNF"},
    # CONSERVE (R5) — rain_soon + wear >= 70
    {"w":"rain_soon","wear":72, "lap":19, "gap":4.0, "sc":False, "tr":0, "act":2, "r":"R5: rain_soon+wear>=70, conserve to merge"},
    {"w":"rain_soon","wear":80, "lap":16, "gap":20.0,"sc":False, "tr":0, "act":2, "r":"R5: rain_soon+wear>=70, conserve"},
    # STAY (R6) — rain_soon + wear < 70
    {"w":"rain_soon","wear":40, "lap":5,  "gap":1.0, "sc":False, "tr":0, "act":1, "r":"R6: rain_soon+wear<70, hold position"},
    {"w":"rain_soon","wear":60, "lap":20, "gap":12.0,"sc":False, "tr":0, "act":1, "r":"R6: rain_soon+wear<70, stay"},
    # CONSERVE (R7) — high traffic stalemate
    {"w":"clear",    "wear":38, "lap":10, "gap":0.6, "sc":False, "tr":2, "act":2, "r":"R7: high traffic stalemate, conserve"},
    # CONSERVE (R8) — clear + wear 60-85 + gap >= 5
    {"w":"clear",    "wear":65, "lap":15, "gap":15.0,"sc":False, "tr":0, "act":2, "r":"R8: clear+60-85+gap>=5, conserve"},
    {"w":"clear",    "wear":74, "lap":24, "gap":6.0, "sc":False, "tr":0, "act":2, "r":"R8: clear+60-85+gap>=5, conserve"},
    # PUSH (R9) — clear + wear<50 + gap<2 + traffic<2
    {"w":"clear",    "wear":25, "lap":9,  "gap":0.3, "sc":False, "tr":0, "act":3, "r":"R9: good tyres+tight gap, push"},
    {"w":"clear",    "wear":45, "lap":21, "gap":1.5, "sc":False, "tr":1, "act":3, "r":"R9: fresh+gap<2+traffic=med, push"},
    # STAY (R10) — default
    {"w":"clear",    "wear":50, "lap":18, "gap":4.0, "sc":False, "tr":0, "act":1, "r":"R10: wear at boundary, default stay"},
]
for d in medium:
    dataset.append({
        "state": {"lap_number":d["lap"],"tyre_wear":d["wear"],"weather":d["w"],"gap_to_car":d["gap"],"safety_car":d["sc"],"traffic_level":d["tr"]},
        "optimal_action":d["act"], "difficulty":"medium", "metadata":{"reason":d["r"],"edge_case":False}
    })

# ----------------------------------------------------------------
# TASK 3  —  HARD  (4 sequences × 3 steps = 12 scenarios)
# ----------------------------------------------------------------
# Each sequence has a unique ID.  Steps within a sequence are linked
# by evolving wear; external world state (weather/SC/traffic) updates
# each step to simulate a dynamic race.
# Rules in play: R1–R9 (all)
hard_sequences = [

    # ── H1: SAFETY CAR WINDOW ────────────────────────────────
    # Race context: SC comes out at lap 15 (wear=62). Optimal to pit
    # cheaply now. After pit, SC still active → stay on fresh tyres.
    # SC ends at lap 17 → push into clean air.
    {
        "id": "H1",
        "steps": [
            # Wear 62, SC active → R3: pit (cheap window)
            {"lap":15,"wear":62,"weather":"clear","gap":5.0,"sc":True, "tr":0,"act":0,"r":"R3: SC active + wear>=55 → cheap pit"},
            # Fresh tyres (0), SC still active → R4: stay (no point pitting again)
            {"lap":16,"wear":2, "weather":"clear","gap":15.0,"sc":True, "tr":0,"act":1,"r":"R4: SC still active, wear<55 (fresh), stay"},
            # SC ends, fresh tyres, rivals right behind → R9: push (gap 0.8 << 2.0 threshold)
            {"lap":17,"wear":7, "weather":"clear","gap":0.8,"sc":False,"tr":0,"act":3,"r":"R9: SC ended, wear<50, gap(0.8)<2.0, traffic=0 → push"},
        ]
    },

    # ── H2: TRAFFIC STALEMATE → ESCAPE ───────────────────────
    # Race context: stuck behind slow car in high traffic.
    # Pushing is useless in traffic → conserve to save tyres.
    # Traffic clears at step 3 → push to take advantage.
    {
        "id": "H2",
        "steps": [
            # High traffic + gap=0.6 → R7: conserve (stalemate)
            {"lap":10,"wear":38,"weather":"clear","gap":0.6,"sc":False,"tr":2,"act":2,"r":"R7: high traffic stalemate → conserve"},
            # Still stuck in traffic + gap=0.5 → R7: conserve again
            {"lap":11,"wear":41,"weather":"clear","gap":0.5,"sc":False,"tr":2,"act":2,"r":"R7: high traffic still → conserve"},
            # Traffic cleared (low), gap still 0.5, wear<50 → R9: push
            {"lap":12,"wear":44,"weather":"clear","gap":0.5,"sc":False,"tr":0,"act":3,"r":"R9: traffic cleared, fresh tyres, gap<2 → push"},
        ]
    },

    # ── H3: SURVIVING HIGH WEAR TO RACE END ──────────────────
    # Race context: wear is climbing in the 70-80% zone.
    # Must conserve to extend stint; wear eventually crosses 86 → pit.
    {
        "id": "H3",
        "steps": [
            # Wear 70, clear, gap=9.0 → R8: conserve (60-85 band, gap>=5)
            {"lap":22,"wear":70,"weather":"clear","gap":9.0,"sc":False,"tr":0,"act":2,"r":"R8: wear in 60-85, gap>=5 → conserve"},
            # Wear 74, still in band, gap=9.5 → R8: conserve
            {"lap":23,"wear":74,"weather":"clear","gap":9.5,"sc":False,"tr":0,"act":2,"r":"R8: still 60-85, gap>=5 → conserve"},
            # Tyre fully degraded → R2: pit (wear=92 >> 86 threshold, no ambiguity)
            {"lap":24,"wear":92,"weather":"clear","gap":10.0,"sc":False,"tr":0,"act":0,"r":"R2: wear(92)>=86, mandatory pit regardless of gap."},
        ]
    },

    # ── H4: THE RAIN BAIT ─────────────────────────────────────
    # Race context: rain is forecast. Tyres getting old (70-78%).
    # Don't pit for slicks — wait for rain to swap to wets in one stop.
    {
        "id": "H4",
        "steps": [
            # Rain soon + wear 72 → R5: conserve (survive for wet-swap)
            {"lap":18,"wear":72,"weather":"rain_soon","gap":6.0,"sc":False,"tr":0,"act":2,"r":"R5: rain_soon + wear>=70 → conserve to merge stop"},
            # Rain soon + wear 76 → R5: conserve (still waiting)
            {"lap":19,"wear":76,"weather":"rain_soon","gap":6.5,"sc":False,"tr":0,"act":2,"r":"R5: rain_soon + wear>=70 → conserve"},
            # Rain arrives! → R1: swap immediately (overrides all)
            {"lap":20,"wear":80,"weather":"rain",     "gap":7.0,"sc":False,"tr":0,"act":4,"r":"R1: rain arrived → swap to wets"},
        ]
    },
]

for seq in hard_sequences:
    for step_i, step in enumerate(seq["steps"]):
        dataset.append({
            "state": {
                "lap_number":  step["lap"],
                "tyre_wear":   step["wear"],
                "weather":     step["weather"],
                "gap_to_car":  step["gap"],
                "safety_car":  step["sc"],
                "traffic_level": step["tr"],
            },
            "optimal_action": step["act"],
            "difficulty": "hard",
            "metadata": {
                "sequence_id": seq["id"],
                "step": step_i,
                "reason": step["r"],
                "edge_case": False,
            }
        })

# ── Validation summary ─────────────────────────────────────────
action_names = {0:"pit", 1:"stay", 2:"conserve", 3:"push", 4:"swap"}
total = len(dataset)
print(f"Total scenarios: {total}  (Easy=10, Medium=15, Hard=12)")
actions = [d["optimal_action"] for d in dataset]
for a, name in action_names.items():
    pct = actions.count(a) / total * 100
    print(f"  Action {a} ({name:8s}): {actions.count(a):3d}  ({pct:.0f}%)")

# ── Export ─────────────────────────────────────────────────────
os.makedirs("data", exist_ok=True)
with open("data/scenarios.json", "w") as f:
    json.dump(dataset, f, indent=4)

flat = [{
    "lap": d["state"]["lap_number"], "wear": d["state"]["tyre_wear"],
    "weather": d["state"]["weather"], "gap": d["state"]["gap_to_car"],
    "safety_car": d["state"]["safety_car"], "traffic": d["state"]["traffic_level"],
    "action": d["optimal_action"], "difficulty": d["difficulty"],
    "reason": d["metadata"]["reason"],
} for d in dataset]
pd.DataFrame(flat).to_csv("data/scenarios.csv", index=False)
pd.DataFrame(flat).to_excel("data/scenarios.xlsx", index=False)
print("Exported: scenarios.json / .csv / .xlsx")
