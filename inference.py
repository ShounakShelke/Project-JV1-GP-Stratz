import os
import json
import textwrap
from openai import OpenAI

from env.race_env import RaceEnvironment

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

def run_inference():
    # Load Environment variables
    api_key = os.environ.get("HF_TOKEN") or os.environ.get("API_KEY")
    base_url = os.environ.get("API_BASE_URL")
    model_name = os.environ.get("MODEL_NAME", "gpt-4o-mini")
    
    if os.environ.get("LOCAL_IMAGE_NAME"):
        model_name = os.environ.get("LOCAL_IMAGE_NAME")

    # Configure OpenAI Client
    client_args = {}
    if base_url:
        client_args["base_url"] = base_url
    if api_key:
        client_args["api_key"] = api_key
    else:
        client_args["api_key"] = "dummy"

    client = OpenAI(**client_args)

    # Initialize environment
    env = RaceEnvironment(max_laps=30)
    state = env.reset()
    
    task_name = "GP-Stratz-Benchmark"
    env_name = "GP-Stratz"
    step_number = 0
    reward_list = []
    total_score = 0.0
    error_msg = None
    success = False
    
    # [START] line - REQUIRED FORMAT
    start_info = {"env": env_name, "model": model_name, "task": task_name}
    print(f'[START] {json.dumps(start_info)}', flush=True)
    
    try:
        while not env.done:
            step_number += 1
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
                        action = 1
                except (ValueError, TypeError):
                    action = 1 
            except Exception:
                action = 1 
            
            # Step the environment
            next_state, raw_reward, done, info = env.step(action)
            total_score += raw_reward
            reward_list.append(round(raw_reward, 4))
            
            # [STEP] line - REQUIRED FORMAT
            step_info = {
                "step": step_number, 
                "action": action, 
                "reward": round(raw_reward, 4), 
                "done": done
            }
            print(f'[STEP] {json.dumps(step_info)}', flush=True)
            
            state = next_state

        success = True
    except Exception as e:
        error_msg = str(e)
        success = False
    finally:
        # [END] line - REQUIRED FORMAT
        end_info = {
            "task": task_name,
            "env": env_name,
            "model": model_name,
            "score": round(total_score, 4),
            "success": success,
            "error": error_msg,
            "reward_list": reward_list
        }
        print(f'[END] {json.dumps(end_info)}', flush=True)

if __name__ == "__main__":
    run_inference()
