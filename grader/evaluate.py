import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from env.race_env import RaceEnvironment

# ─────────────────────────────────────────────────────────────────────────────
# WEATHER CONVERSION  (dataset strings → env int constants)
# ─────────────────────────────────────────────────────────────────────────────
WEATHER_MAP = {
    "clear":     RaceEnvironment.WEATHER_CLEAR,
    "rain_soon": RaceEnvironment.WEATHER_SOON,
    "rain":      RaceEnvironment.WEATHER_RAIN,
}

# ─────────────────────────────────────────────────────────────────────────────
# BASELINE AGENT  —  strict rule hierarchy (mirrors generate_data.py rules)
# ─────────────────────────────────────────────────────────────────────────────
def choose_action(state):
    """
    Priority-ordered rule-based agent.
    Rules are IDENTICAL to the golden rules in generate_data.py and race_env.py.

    R1  weather == RAIN          → Swap (4)
    R2  wear >= 86               → Pit  (0)
    R3  rain_soon & wear >= 70   → Conserve (2)
    R4  rain_soon & wear < 70    → Stay out (1)
    R5  clear, wear 60-85, gap>=5→ Conserve (2)
    R6  wear < 50, gap < 2       → Push (3)
    R7  wear < 50                → Stay out (1)
    R8  wear 50-60               → Stay out (1)
    R9  fallback                 → Stay out (1)
    """
    wear    = state["tyre_wear"]
    weather = state["weather"]   # int constant
    gap     = state["gap_to_car"]

    # R1 – rain is mandatory swap
    if weather == RaceEnvironment.WEATHER_RAIN:
        return RaceEnvironment.ACTION_SWAP

    # R2 – tyre failure imminent
    if wear >= RaceEnvironment.WEAR_PIT_THRESHOLD:
        return RaceEnvironment.ACTION_PIT

    # R3 – rain coming, save tyres to merge with tyre-change stop
    if weather == RaceEnvironment.WEATHER_SOON and wear >= RaceEnvironment.WEAR_RAIN_SOON_CONSERVE:
        return RaceEnvironment.ACTION_CONSERVE

    # R4 – rain coming but tyres are fine, just hold position
    if weather == RaceEnvironment.WEATHER_SOON:
        return RaceEnvironment.ACTION_STAY

    # R5 – clear weather, wear is moderate-high, big enough gap to slow down
    if (RaceEnvironment.WEAR_CONSERVE_LOW <= wear <= RaceEnvironment.WEAR_CONSERVE_HIGH
            and gap >= RaceEnvironment.GAP_CONSERVE_THRESHOLD):
        return RaceEnvironment.ACTION_CONSERVE

    # R6 – fresh tyres and rival is right there
    if wear < 50 and gap < RaceEnvironment.GAP_PUSH_THRESHOLD:
        return RaceEnvironment.ACTION_PUSH

    # R7 / R8 / R9 – safe to cruise
    return RaceEnvironment.ACTION_STAY


# ─────────────────────────────────────────────────────────────────────────────
# DATASET LOADER
# ─────────────────────────────────────────────────────────────────────────────
def load_dataset(filepath="data/scenarios.json"):
    if not os.path.exists(filepath):
        print(f"[ERROR] Dataset not found at '{filepath}'.")
        print("Run:  python data/generate_data.py")
        return []
    with open(filepath, "r") as f:
        return json.load(f)


# ─────────────────────────────────────────────────────────────────────────────
# EVALUATION LOOP
# ─────────────────────────────────────────────────────────────────────────────
def run_evaluation():
    dataset = load_dataset()
    if not dataset:
        return

    env = RaceEnvironment(max_laps=30)

    total_reward  = 0.0
    max_reward    = 0.0   # best-case = every action correct (+1.0 correctness + max bonus)
    matches       = 0
    pass_rewards  = []
    fail_rewards  = []

    print(f"GP-Stratz Evaluation  |  {len(dataset)} scenarios")
    print("=" * 55)

    for i, scenario in enumerate(dataset):
        s      = scenario["state"]
        opt    = scenario["optimal_action"]
        diff   = scenario["difficulty"].upper()

        # Reset env to exactly the scenario starting state
        state = env.reset({
            "lap":       s["lap_number"],
            "wear":      s["tyre_wear"],
            "weather":   WEATHER_MAP[s["weather"]],
            "gap":       s["gap_to_car"],
            "tyre_type": RaceEnvironment.TYRE_SLICKS,   # default
        })

        # Agent decision (rule-based baseline)
        agent_action = choose_action(state)

        # Step the environment WITH the optimal label so reward aligns
        _, reward, _, info = env.step(agent_action, optimal_action=opt)

        total_reward += reward
        max_reward   += 1.5            # correctness(1.0) + max bonus(0.5)

        if agent_action == opt:
            matches += 1
            status   = "PASS"
            pass_rewards.append(reward)
        else:
            status = f"FAIL (want {opt}, got {agent_action})"
            fail_rewards.append(reward)

        print(f"  #{i+1:02d} [{diff:6s}] {status:<28} reward={reward:+.3f}")

    # ── Summary ──────────────────────────────────────────────
    accuracy       = (matches / len(dataset)) * 100
    norm_score     = total_reward / max_reward if max_reward else 0.0
    avg_pass_r     = sum(pass_rewards) / len(pass_rewards)   if pass_rewards else 0
    avg_fail_r     = sum(fail_rewards) / len(fail_rewards)   if fail_rewards else 0

    print("\n" + "=" * 55)
    print("EVALUATION COMPLETE")
    print(f"  Accuracy        : {accuracy:.1f}%  ({matches}/{len(dataset)})")
    print(f"  Total Reward    : {total_reward:.2f}")
    print(f"  Normalised Score: {norm_score:.3f}   (range 0.0 – 1.0)")
    print(f"  Avg PASS reward : {avg_pass_r:+.3f}")
    print(f"  Avg FAIL reward : {avg_fail_r:+.3f}")
    print("=" * 55)

    if avg_pass_r > avg_fail_r:
        print("[OK] PASS rewards are consistently higher than FAIL rewards.")
    else:
        print("[WARN] Reward alignment issue detected — review env.step().")


if __name__ == "__main__":
    run_evaluation()
