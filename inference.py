import os
import json
import textwrap
from openai import OpenAI
from env.race_env import RaceEnvironment
from grader.evaluate import load_dataset, normalize_score, WEATHER_MAP

def get_system_prompt():
    return textwrap.dedent("""\
        You are an expert motorsport strategist.
        Given the current state of a race, you must return an integer from 0 to 4 representing the best action.
        
        0: PIT
        1: STAY
        2: CONSERVE
        3: PUSH
        4: SWAP
        
        Rules:
        - Rain means swap tyres.
        - High wear means pit.
        - Otherwise, manage the gap and wear efficiently.
        
        Output ONLY the numeric action (0, 1, 2, 3, or 4). Do not provide any explanation.
    """)

def get_llm_action(client, model_name, state):
    prompt = f"Current state: {json.dumps(state)}"
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": get_system_prompt()},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=10
        )
        output = response.choices[0].message.content.strip()
        try:
            action = int(output)
            if action not in [0, 1, 2, 3, 4]:
                return 1
            return action
        except (ValueError, TypeError):
            return 1
    except Exception:
        return 1

def run_inference():
    # Environment variables
    api_key = os.getenv("HF_TOKEN")
    base_url = os.getenv("API_BASE_URL", "https://api-inference.huggingface.co/v1")
    model_name = os.getenv("MODEL_NAME", "gpt-4o-mini")
    
    if os.environ.get("LOCAL_IMAGE_NAME"):
        model_name = os.environ.get("LOCAL_IMAGE_NAME")

    # OpenAI Client
    client_args = {"api_key": api_key if api_key else "dummy"}
    if base_url:
        client_args["base_url"] = base_url
    client = OpenAI(**client_args)

    # Initialize environment and dataset
    dataset = load_dataset()
    if not dataset:
        print('[ERROR] No dataset found.')
        return

    env = RaceEnvironment(max_laps=30)
    
    # 3 Task Logic
    task_stats = {
        "easy":   {"reward": 0.0, "max": 0.0},
        "medium": {"reward": 0.0, "max": 0.0},
        "hard":   {"reward": 0.0, "max": 0.0}
    }
    
    # [START] - REQUIRED FORMAT
    task_name = "GP-Stratz-Benchmark"
    env_name = "GP-Stratz"
    print(f"[START] task={task_name} env={env_name} model={model_name}", flush=True)
    
    step_number = 0
    current_seq = None
    all_rewards = []

    for scenario in dataset:
        diff = scenario["difficulty"]
        s    = scenario["state"]
        opt  = scenario["optimal_action"]
        meta = scenario.get("metadata", {})
        seq  = meta.get("sequence_id")

        # Sync environment state
        if diff == "hard" and seq == current_seq:
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

        # Get LLM action
        action = get_llm_action(client, model_name, state)
        
        # Step env
        _, reward, done, _ = env.step(action, optimal_action=opt)
        
        # Update metrics
        task_stats[diff]["reward"] += reward
        task_stats[diff]["max"] += 1.0
        step_number += 1
        all_rewards.append(reward)
        
        # [STEP] - REQUIRED FORMAT
        bool_done = str(done).lower()
        print(f"[STEP] step={step_number} action={action} reward={reward:.2f} done={bool_done} error=null", flush=True)

    # Compile Final Tasks scores
    easy_score   = normalize_score(task_stats["easy"]["reward"] / task_stats["easy"]["max"])
    medium_score = normalize_score(task_stats["medium"]["reward"] / task_stats["medium"]["max"])
    hard_score   = normalize_score(task_stats["hard"]["reward"] / task_stats["hard"]["max"])
    
    overall_score = normalize_score((easy_score + medium_score + hard_score) / 3.0)

    # [END] - UPDATED Phase 2 FORMAT
    rewards_str = ",".join(f"{r:.2f}" for r in all_rewards)
    print(f"[END] success=true steps={step_number} score={overall_score:.2f} rewards={rewards_str}", flush=True)

if __name__ == "__main__":
    run_inference()
