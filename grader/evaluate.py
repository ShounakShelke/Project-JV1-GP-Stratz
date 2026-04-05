import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from env.race_env import RaceEnvironment

WEATHER_MAP = {"clear": 0, "rain_soon": 1, "rain": 2}

# ═══════════════════════════════════════════════════════════════════
#  GP-Stratz Baseline Agent  v4
# ═══════════════════════════════════════════════════════════════════
#  10 RULES — strictly ordered, mutually exclusive.
#  Identical thresholds to env/race_env.py and data/generate_data.py
#
#  R1   weather==RAIN                           → SWAP
#  R2   wear >= WEAR_CRITICAL (86)              → PIT
#  R3   safety_car==True  AND  wear >= 55       → PIT     (cheap)
#  R4   safety_car==True  AND  wear <  55       → STAY    (fresh, skip)
#  R5   weather==RAIN_SOON  AND  wear >= 70     → CONSERVE
#  R6   weather==RAIN_SOON  AND  wear <  70     → STAY
#  R7   traffic==HIGH  AND  gap <= 1.0          → CONSERVE (stalemate)
#  R8   clear + 60<=wear<=85 + gap>=5.0         → CONSERVE (stretch)
#  R9   clear + wear<50 + gap<2.0 + traffic<2   → PUSH
#  R10  default                                 → STAY
# ═══════════════════════════════════════════════════════════════════

def baseline_agent(state):
    wear    = state["tyre_wear"]
    weather = state["weather"]     # int from env._obs()
    gap     = state["gap_to_car"]
    sc      = state.get("safety_car", False)
    traffic = state.get("traffic_level", 0)

    # R1 — Rain: swap immediately regardless of anything else
    if weather == RaceEnvironment.WEATHER_RAIN:
        return RaceEnvironment.ACTION_SWAP

    # R2 — Critical wear: mandatory pit
    if wear >= RaceEnvironment.WEAR_CRITICAL:
        return RaceEnvironment.ACTION_PIT

    # R3 — Safety car + moderate+ wear: cheap pit window
    if sc and wear >= RaceEnvironment.WEAR_SC_PIT:
        return RaceEnvironment.ACTION_PIT

    # R4 — Safety car + fresh tyres: no point pitting
    if sc and wear < RaceEnvironment.WEAR_SC_PIT:
        return RaceEnvironment.ACTION_STAY

    # R5 — Rain coming + wear high: survive for wet swap stop
    if weather == RaceEnvironment.WEATHER_SOON and wear >= RaceEnvironment.WEAR_RAIN_SOON_CONSERVE:
        return RaceEnvironment.ACTION_CONSERVE

    # R6 — Rain coming + wear low: just hold
    if weather == RaceEnvironment.WEATHER_SOON:
        return RaceEnvironment.ACTION_STAY

    # R7 — High traffic stalemate: can't pass, save rubber
    if traffic == RaceEnvironment.TRAFFIC_HIGH and gap <= RaceEnvironment.GAP_PUSH:
        return RaceEnvironment.ACTION_CONSERVE

    # R8 — Clear sky + moderate wear band + safe gap: stretch the stint
    if (weather == RaceEnvironment.WEATHER_CLEAR
            and RaceEnvironment.WEAR_CONSERVE_MIN <= wear <= RaceEnvironment.WEAR_CONSERVE_MAX
            and gap >= RaceEnvironment.GAP_CONSERVE):
        return RaceEnvironment.ACTION_CONSERVE

    # R9 — Clear + fresh tyres + rival right there + not gridlocked
    if (weather == RaceEnvironment.WEATHER_CLEAR
            and wear < 50
            and gap < RaceEnvironment.GAP_PUSH
            and traffic < RaceEnvironment.TRAFFIC_HIGH):
        return RaceEnvironment.ACTION_PUSH

    # R10 — Default: cruise
    return RaceEnvironment.ACTION_STAY


# ───────────────────────────────────────────────────────────────────
def load_dataset(filepath="data/dataset.json"):
    if not os.path.exists(filepath):
        print(f"[ERROR] Dataset not found at '{filepath}'")
        print("Run:  python data/generate_data.py")
        return []
    with open(filepath) as f:
        return json.load(f)


# ───────────────────────────────────────────────────────────────────
def run_evaluation():
    dataset = load_dataset()
    if not dataset:
        return

    env = RaceEnvironment(max_laps=30)

    total_reward  = 0.0
    max_reward    = 0.0
    matches       = 0
    task_scores   = {"easy":[0.0,0], "medium":[0.0,0], "hard":[0.0,0]}
    pass_rewards  = []
    fail_rewards  = []

    print(f"GP-Stratz Evaluation v4  |  {len(dataset)} scenarios")
    print("=" * 60)

    current_seq  = None

    for i, scenario in enumerate(dataset):
        s    = scenario["state"]
        opt  = scenario["optimal_action"]
        diff = scenario["difficulty"]
        meta = scenario.get("metadata", {})
        seq  = meta.get("sequence_id")

        # ── State initialisation ──────────────────────────────
        # Design principle: the dataset encodes the EXACT ground-truth
        # state at every step (including wear & gap). We always load it
        # fully. For Hard sequences this means the dataset pre-computes
        # the expected wear after each action, which keeps every step's
        # decision boundary crisp and unambiguous.
        if diff == "hard" and seq == current_seq:
            # Sequence continuation: update ALL state vars from dataset.
            # This ensures the agent sees the intended state at each step,
            # not a drift from the env's own physics approximation.
            env.lap        = s["lap_number"]
            env.wear       = float(s["tyre_wear"])
            env.weather    = WEATHER_MAP.get(s["weather"], 0)
            env.gap        = float(s["gap_to_car"])
            env.safety_car = bool(s.get("safety_car", False))
            env.traffic    = s.get("traffic_level", 0)
            state = env._obs()
        else:
            current_seq = seq
            state = env.reset({
                "lap":        s["lap_number"],
                "wear":       s["tyre_wear"],
                "weather":    WEATHER_MAP.get(s["weather"], 0),
                "gap":        s["gap_to_car"],
                "safety_car": bool(s.get("safety_car", False)),
                "traffic":    s.get("traffic_level", 0),
                "tyre_type":  0,
            })

        # ── Agent decision ────────────────────────────────────
        action = baseline_agent(state)

        # ── Step env (pass label so reward aligns) ────────────
        _, reward, _, info = env.step(action, optimal_action=opt)

        # ── Bookkeeping ───────────────────────────────────────
        total_reward += reward
        max_reward   += 1.6     # correctness(1.2) + max forward_bonus(0.4)
        task_scores[diff][0] += reward
        task_scores[diff][1] += 1

        if action == opt:
            matches += 1
            status = "PASS"
            pass_rewards.append(reward)
        else:
            status = f"FAIL (want {opt}, got {action})"
            fail_rewards.append(reward)

        print(f"  #{i+1:02d} [{diff:6s}] {status:<30} reward={reward:+.3f}")

    # ── Summary ───────────────────────────────────────────────
    accuracy   = matches / len(dataset) * 100
    norm_score = total_reward / max_reward if max_reward else 0.0
    avg_pass   = sum(pass_rewards) / len(pass_rewards) if pass_rewards else 0
    avg_fail   = sum(fail_rewards) / len(fail_rewards) if fail_rewards else 0

    print("\n" + "=" * 60)
    print("GP-STRATZ FINAL RESULTS")
    print("=" * 60)
    print(f"  Global Accuracy   : {accuracy:.1f}%  ({matches}/{len(dataset)})")
    print(f"  Normalised Score  : {norm_score:.3f}   (0.0–1.0 scale)")
    print(f"  Avg PASS reward   : {avg_pass:+.3f}")
    print(f"  Avg FAIL reward   : {avg_fail:+.3f}")
    print()
    print("  Task breakdown:")
    for t, (r, c) in task_scores.items():
        print(f"    {t.upper():8s}: avg reward = {r/c:+.3f}  ({c} steps)")
    print("=" * 60)

    if avg_pass > avg_fail:
        print("[OK] PASS rewards consistently higher than FAIL rewards.")
    else:
        print("[WARN] Alignment issue — review env.step() reward design.")


if __name__ == "__main__":
    run_evaluation()
