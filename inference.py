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
        # Fallback dummy key to prevent client crash if testing locally against a local proxy
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
    
    # Start line
    print(f'{{"type": "start", "env": "{env_name}", "model": "{model_name}", "task": "{task_name}"}}', flush=True)
    
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
                
                # Parse action safely
                try:
                    action = int(output)
                    if action not in [0, 1, 2, 3, 4]:
                        action = 1 # Fallback to STAY
                except ValueError:
                    action = 1 # Fallback
            except Exception as e:
                action = 1 # Default conservative fallback
                # We could record error, but we want to finish the episode
            
            # Step the environment
            next_state, reward, done, info = env.step(action)
            
            total_score += reward
            reward_list.append(round(reward, 2))
            
            # Step line
            done_str = "true" if done else "false"
            print(f'{{"type": "step", "step": {step_number}, "action": {action}, "reward": {reward:.2f}, "done": {done_str}}}', flush=True)
            
            state = next_state

        success = True
    except Exception as e:
        error_msg = str(e)
        success = False
    finally:
        success_str = "true" if success else "false"
        error_val = json.dumps(error_msg) if error_msg else "null"
        # End line
        print(f'{{"type": "end", "task": "{task_name}", "env": "{env_name}", "model": "{model_name}", "score": {total_score:.2f}, "success": {success_str}, "error": {error_val}, "reward_list": {reward_list}}}', flush=True)

if __name__ == "__main__":
    run_inference()
