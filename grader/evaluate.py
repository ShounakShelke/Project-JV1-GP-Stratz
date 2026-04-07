import json
import os
import sys

# Ensure parent directory is in path for 'env' etc.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from env.race_env import RaceEnvironment

WEATHER_MAP = {"clear": 0, "rain_soon": 1, "rain": 2}

def baseline_agent(state):
    wear    = state["tyre_wear"]
    weather = state["weather"]
    gap     = state["gap_to_car"]
    sc      = state.get("safety_car", False)
    traffic = state.get("traffic_level", 0)

    if weather == RaceEnvironment.WEATHER_RAIN:
        return RaceEnvironment.ACTION_SWAP
    if wear >= RaceEnvironment.WEAR_CRITICAL:
        return RaceEnvironment.ACTION_PIT
    if sc and wear >= RaceEnvironment.WEAR_SC_PIT:
        return RaceEnvironment.ACTION_PIT
    if sc and wear < RaceEnvironment.WEAR_SC_PIT:
        return RaceEnvironment.ACTION_STAY
    if weather == RaceEnvironment.WEATHER_SOON and wear >= RaceEnvironment.WEAR_RAIN_SOON_CONSERVE:
        return RaceEnvironment.ACTION_CONSERVE
    if weather == RaceEnvironment.WEATHER_SOON:
        return RaceEnvironment.ACTION_STAY
    if traffic == RaceEnvironment.TRAFFIC_HIGH and gap <= RaceEnvironment.GAP_PUSH:
        return RaceEnvironment.ACTION_CONSERVE
    if (weather == RaceEnvironment.WEATHER_CLEAR
            and RaceEnvironment.WEAR_CONSERVE_MIN <= wear <= RaceEnvironment.WEAR_CONSERVE_MAX
            and gap >= RaceEnvironment.GAP_CONSERVE):
        return RaceEnvironment.ACTION_CONSERVE
    if (weather == RaceEnvironment.WEATHER_CLEAR
            and wear < 50
            and gap < RaceEnvironment.GAP_PUSH
            and traffic < RaceEnvironment.TRAFFIC_HIGH):
        return RaceEnvironment.ACTION_PUSH
    return RaceEnvironment.ACTION_STAY

def normalize_score(score):
    """Ensures score is strictly (0, 1)."""
    if score >= 1.0: return 0.999
    if score <= 0.0: return 0.001
    return round(float(score), 4)

def evaluate_task(difficulty, dataset, agent_fn=None):
    if agent_fn is None:
        agent_fn = baseline_agent
        
    env = RaceEnvironment(max_laps=30)
    task_reward = 0.0
    task_max = 0.0
    current_seq = None

    filtered_data = [s for s in dataset if s["difficulty"] == difficulty]
    if not filtered_data:
        return 0.5

    for scenario in filtered_data:
        s    = scenario["state"]
        opt  = scenario["optimal_action"]
        meta = scenario.get("metadata", {})
        seq  = meta.get("sequence_id")

        if difficulty == "hard" and seq == current_seq:
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

        action = agent_fn(state)
        _, reward, _, _ = env.step(action, optimal_action=opt)

        task_reward += reward
        task_max += 1.0

    raw_score = task_reward / task_max if task_max > 0 else 0.5
    return normalize_score(raw_score)

def evaluate_easy(dataset, agent_fn=None):
    return evaluate_task("easy", dataset, agent_fn)

def evaluate_medium(dataset, agent_fn=None):
    return evaluate_task("medium", dataset, agent_fn)

def evaluate_hard(dataset, agent_fn=None):
    return evaluate_task("hard", dataset, agent_fn)

def load_dataset(filepath="data/dataset.json"):
    if not os.path.exists(filepath):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        filepath = os.path.join(base_dir, "data", "dataset.json")
    if not os.path.exists(filepath):
        return []
    with open(filepath) as f:
        return json.load(f)

def run_evaluation():
    dataset = load_dataset()
    if not dataset:
        return {"error": "no data"}
    
    e = evaluate_easy(dataset)
    m = evaluate_medium(dataset)
    h = evaluate_hard(dataset)
    ov = normalize_score((e + m + h) / 3.0)
    
    res = {"score": ov, "tasks": {"easy": e, "medium": m, "hard": h}}
    if __name__ == "__main__":
        print(json.dumps(res, indent=2))
    return res

if __name__ == "__main__":
    run_evaluation()
