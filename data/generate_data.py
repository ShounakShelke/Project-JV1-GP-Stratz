import json
import pandas as pd
import os

# ============================================================
# GP-Stratz Dataset v2  |  FIXED: strict deterministic rules
# ============================================================
#
# GOLDEN RULES (in priority order — applied top-to-bottom)
# ─────────────────────────────────────────────────────────
# R1  weather == "rain"            → ACTION 4 (swap)          [hard override]
# R2  tyre_wear >= 86              → ACTION 0 (pit)            [safety]
# R3  weather == "rain_soon"
#       & wear  >= 70              → ACTION 2 (conserve)       [wait for rain]
# R4  weather == "rain_soon"
#       & wear  <  70              → ACTION 1 (stay out)       [wait for rain]
# R5  tyre_wear 60–85
#       & gap   >= 5.0             → ACTION 2 (conserve)       [protect life]
# R6  tyre_wear <  50
#       & gap   <  2.0             → ACTION 3 (push)           [attack]
# R7  tyre_wear <  50              → ACTION 1 (stay out)       [normal]
# R8  tyre_wear 50–60              → ACTION 1 (stay out)       [acceptable]
# R9  fallback                     → ACTION 1 (stay out)
#
# These rules are IDENTICAL inside choose_action() in evaluate.py
# ============================================================

dataset = []

# ── TASK 1 : EASY (20 samples) ──────────────────────────────
# Scope: weather = "clear" only. Decisions driven by wear + gap.
# Rules in play: R5, R6, R7, R8, R2
easy_data = [
    # --- Stay Out (R7 / R8) --- low/moderate wear, clear, safe gap ---
    {"wear": 10, "lap": 1,  "gap": 5.0,  "action": 1, "reason": "R7: wear<50, clear. Stay out."},
    {"wear": 20, "lap": 5,  "gap": 3.0,  "action": 1, "reason": "R7: wear<50, clear. Stay out."},
    {"wear": 30, "lap": 10, "gap": 4.5,  "action": 1, "reason": "R7: wear<50, clear. Stay out."},
    {"wear": 45, "lap": 15, "gap": 2.5,  "action": 1, "reason": "R7: wear<50, gap>=2. Stay out."},
    {"wear": 55, "lap": 20, "gap": 6.0,  "action": 1, "reason": "R8: wear 50-60, clear. Stay out."},
    {"wear": 58, "lap": 24, "gap": 5.0,  "action": 1, "reason": "R8: wear 50-60, clear. Stay out."},

    # --- Conserve (R5) --- wear 60-85, gap >= 5 ---
    {"wear": 62, "lap": 18, "gap": 8.0,  "action": 2, "reason": "R5: wear 60-85, gap>=5. Conserve."},
    {"wear": 70, "lap": 22, "gap": 15.0, "action": 2, "reason": "R5: wear 60-85, gap>=5. Conserve."},
    {"wear": 75, "lap": 25, "gap": 7.0,  "action": 2, "reason": "R5: wear 60-85, gap>=5. Conserve."},
    {"wear": 80, "lap": 27, "gap": 20.0, "action": 2, "reason": "R5: wear 60-85, gap>=5. Conserve."},

    # --- Push (R6) --- wear < 50, gap < 2 ---
    {"wear": 15, "lap": 2,  "gap": 0.2,  "action": 3, "reason": "R6: wear<50, gap<2. Push.", "edge": True},
    {"wear": 30, "lap": 12, "gap": 1.5,  "action": 3, "reason": "R6: wear<50, gap<2. Push."},
    {"wear": 40, "lap": 18, "gap": 0.8,  "action": 3, "reason": "R6: wear<50, gap<2. Push."},
    {"wear": 48, "lap": 19, "gap": 1.2,  "action": 3, "reason": "R6: wear<50, gap<2. Push."},

    # --- Pit (R2) --- wear >= 86 ---
    {"wear": 86, "lap": 20, "gap": 4.0,  "action": 0, "reason": "R2: wear>=86. Pit immediately."},
    {"wear": 90, "lap": 15, "gap": 2.5,  "action": 0, "reason": "R2: wear>=86. Pit."},
    {"wear": 95, "lap": 26, "gap": 1.0,  "action": 0, "reason": "R2: wear>=86. Pit despite close gap.", "edge": True},
    {"wear": 98, "lap": 29, "gap": 30.0, "action": 0, "reason": "R2: wear>=86. Emergency pit.", "edge": True},
    {"wear": 88, "lap": 10, "gap": 2.0,  "action": 0, "reason": "R2: wear>=86. Unsafe. Pit.", "edge": True},
    {"wear": 92, "lap": 14, "gap": 5.0,  "action": 0, "reason": "R2: wear>=86. Pit."},
]

for d in easy_data:
    dataset.append({
        "state": {"lap_number": d["lap"], "tyre_wear": d["wear"], "weather": "clear", "gap_to_car": d["gap"]},
        "optimal_action": d["action"],
        "difficulty": "easy",
        "metadata": {"reason": d["reason"], "edge_case": d.get("edge", False)}
    })

# ── TASK 2 : MEDIUM (30 samples) ────────────────────────────
# Scope: weather varies. Multi-factor decisions.
# Rules in play: R1-R9 (all)
medium_data = [
    # --- Swap (R1): rain — mandatory tyre change regardless of wear/gap ---
    {"weather": "rain", "wear": 10,  "gap": 5.0,  "lap": 5,  "action": 4, "reason": "R1: rain. Swap immediately."},
    {"weather": "rain", "wear": 20,  "gap": 2.0,  "lap": 10, "action": 4, "reason": "R1: rain. Swap."},
    {"weather": "rain", "wear": 50,  "gap": 2.0,  "lap": 28, "action": 4, "reason": "R1: rain. Must swap."},
    {"weather": "rain", "wear": 80,  "gap": 2.0,  "lap": 15, "action": 4, "reason": "R1: rain + high wear. Swap."},
    {"weather": "rain", "wear": 90,  "gap": 5.0,  "lap": 8,  "action": 4, "reason": "R1: rain. Swap urgently."},
    {"weather": "rain", "wear": 40,  "gap": 15.0, "lap": 12, "action": 4, "reason": "R1: rain. Gap irrelevant. Swap."},

    # --- Pit (R2): wear >= 86 takes priority over rain_soon ---
    {"weather": "rain_soon", "wear": 95, "gap": 10.0, "lap": 20, "action": 0, "reason": "R2 beats R3: wear>=86, pit now.", "edge": True},
    {"weather": "rain_soon", "wear": 92, "gap": 1.0,  "lap": 29, "action": 0, "reason": "R2: wear>=86. Pit or DNF.", "edge": True},
    {"weather": "clear",     "wear": 88, "gap": 5.0,  "lap": 14, "action": 0, "reason": "R2: wear>=86. Pit."},
    {"weather": "clear",     "wear": 86, "gap": 0.5,  "lap": 11, "action": 0, "reason": "R2: wear>=86. Pit despite close gap.", "edge": True},

    # --- Conserve (R3): rain_soon + wear >= 70 → survive for swap ---
    {"weather": "rain_soon", "wear": 70,  "gap": 5.0,  "lap": 12, "action": 2, "reason": "R3: rain_soon, wear>=70. Conserve."},
    {"weather": "rain_soon", "wear": 75,  "gap": 0.5,  "lap": 10, "action": 2, "reason": "R3: rain_soon, wear>=70. Conserve.", "edge": True},
    {"weather": "rain_soon", "wear": 80,  "gap": 20.0, "lap": 16, "action": 2, "reason": "R3: rain_soon, wear>=70. Conserve.", "edge": True},
    {"weather": "rain_soon", "wear": 72,  "gap": 4.0,  "lap": 19, "action": 2, "reason": "R3: rain_soon, wear>=70. Conserve."},

    # --- Stay out (R4): rain_soon + wear < 70 → stay for now ---
    {"weather": "rain_soon", "wear": 40,  "gap": 1.0,  "lap": 5,  "action": 1, "reason": "R4: rain_soon, wear<70. Stay out."},
    {"weather": "rain_soon", "wear": 30,  "gap": 8.0,  "lap": 7,  "action": 1, "reason": "R4: rain_soon, wear<70. Stay out."},
    {"weather": "rain_soon", "wear": 60,  "gap": 12.0, "lap": 20, "action": 1, "reason": "R4: rain_soon, wear<70. Stay out."},
    {"weather": "rain_soon", "wear": 50,  "gap": 0.5,  "lap": 18, "action": 1, "reason": "R4: rain_soon, wear<70. Stay out."},

    # --- Conserve (R5): clear, wear 60-85, gap >= 5 ---
    {"weather": "clear", "wear": 65, "gap": 15.0, "lap": 15, "action": 2, "reason": "R5: clear, wear 60-85, gap>=5. Conserve."},
    {"weather": "clear", "wear": 70, "gap": 3.0,  "lap": 26, "action": 2, "reason": "R5: late race, wear 60-85, gap>=5. Conserve."},
    {"weather": "clear", "wear": 74, "gap": 2.5,  "lap": 24, "action": 2, "reason": "R5: wear 60-85, gap>=5. Conserve."},
    {"weather": "clear", "wear": 68, "gap": 8.0,  "lap": 17, "action": 2, "reason": "R5: wear 60-85, gap>=5. Conserve."},

    # --- Push (R6): clear, wear < 50, gap < 2 ---
    {"weather": "clear", "wear": 15, "gap": 2.0,  "lap": 2,  "action": 3, "reason": "R6: wear<50, gap<2. Push."},
    {"weather": "clear", "wear": 25, "gap": 0.3,  "lap": 9,  "action": 3, "reason": "R6: wear<50, gap<2. Push hard."},
    {"weather": "clear", "wear": 45, "gap": 1.0,  "lap": 21, "action": 3, "reason": "R6: wear<50, gap<2. Push."},

    # --- Stay out (R7/R8): clear, low/moderate wear, safe gap ---
    {"weather": "clear", "wear": 55, "gap": 4.0,  "lap": 18, "action": 1, "reason": "R8: wear 50-60, clear. Stay out."},
    {"weather": "clear", "wear": 45, "gap": 22.0, "lap": 21, "action": 1, "reason": "R7: wear<50, large gap. Stay out."},

    # Additional edge cases
    {"weather": "rain_soon", "wear": 85, "gap": 5.0, "lap": 12, "action": 2, "reason": "R3: wear>=70, rain_soon. Conserve not pit.", "edge": True},
    {"weather": "rain",      "wear": 85, "gap": 0.5, "lap": 25, "action": 4, "reason": "R1: rain overrides everything. Swap.", "edge": True},
]

for d in medium_data:
    dataset.append({
        "state": {"lap_number": d["lap"], "tyre_wear": d["wear"], "weather": d["weather"], "gap_to_car": d["gap"]},
        "optimal_action": d["action"],
        "difficulty": "medium",
        "metadata": {"reason": d["reason"], "edge_case": d.get("edge", False)}
    })

# ── VALIDATION ──────────────────────────────────────────────
print(f"Total scenarios: {len(dataset)}")
actions = [d["optimal_action"] for d in dataset]
for a, name in enumerate(["pit", "stay", "conserve", "push", "swap"]):
    print(f"  Action {a} ({name}): {actions.count(a)}")

# ── EXPORT ──────────────────────────────────────────────────
os.makedirs("data", exist_ok=True)

with open("data/scenarios.json", "w") as f:
    json.dump(dataset, f, indent=4)

flat = [{
    "lap_number":      d["state"]["lap_number"],
    "tyre_wear":       d["state"]["tyre_wear"],
    "weather":         d["state"]["weather"],
    "gap_to_car":      d["state"]["gap_to_car"],
    "optimal_action":  d["optimal_action"],
    "difficulty":      d["difficulty"],
    "reason":          d["metadata"]["reason"],
    "edge_case":       d["metadata"]["edge_case"],
} for d in dataset]

df = pd.DataFrame(flat)
df.to_csv("data/scenarios.csv", index=False)
df.to_excel("data/scenarios.xlsx", index=False)

print("Dataset v2 written to data/scenarios.json, .csv, .xlsx")
