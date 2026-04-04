from env.race_env import RaceEnvironment

def run_simulation():
    print("--- GP Stratz Manual Env Test ---")
    env = RaceEnvironment(max_laps=5)
    
    # Custom initial state
    initial_state = {
        "lap": 1,
        "wear": 80.0,
        "weather": RaceEnvironment.WEATHER_CLEAR,
        "gap": 10.0,
        "tyre_type": RaceEnvironment.TYRE_SLICKS
    }
    
    state = env.reset(initial_state)
    print(f"Start State: {state}")
    
    # We will simulate 5 steps.
    actions = [
        RaceEnvironment.ACTION_STAY,   # Lap 1: Stay out (dangerously high wear)
        RaceEnvironment.ACTION_PIT,    # Lap 2: Pit (Wear was probably too high)
        RaceEnvironment.ACTION_PUSH,   # Lap 3: Push on fresh tyres
        RaceEnvironment.ACTION_CONSERVE, # Lap 4: Conserve
        RaceEnvironment.ACTION_STAY    # Lap 5: Stay Out
    ]
    
    for i, action in enumerate(actions):
        print(f"\n--- Lap {state['lap_number']} ---")
        print(f"Agent Action: {action}")
        
        next_state, reward, done, info = env.step(action)
        
        print(f"Resulting State: {next_state}")
        print(f"Reward: {reward}")
        print(f"Info Breakdown: {info}")
        
        state = next_state
        if done:
            print("\n>>> EPISODE DONE <<<")
            break

if __name__ == "__main__":
    run_simulation()
