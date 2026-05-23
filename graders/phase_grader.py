import sys
import os

# Add parent directory to path so we can import env
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from env.race_env import RaceEnvironment
from agents.hard_agent import HardMultiFactorAgent

PHASE_SCENARIOS = {
    "easy": {
        "wear": 80.0,
        "weather": RaceEnvironment.WEATHER_CLEAR,
        "gap": 5.0,
        "tyre_type": 0,
        "safety_car": False,
        "traffic": RaceEnvironment.TRAFFIC_LOW,
        "deg_rate": 1.0
    },
    "medium": {
        "wear": 50.0,
        "weather": RaceEnvironment.WEATHER_CLEAR,
        "gap": 2.5,
        "tyre_type": 0,
        "safety_car": True,
        "traffic": RaceEnvironment.TRAFFIC_MEDIUM,
        "deg_rate": 1.2
    },
    "hard": {
        "wear": 20.0,
        "weather": RaceEnvironment.WEATHER_SOON,
        "gap": 1.0,
        "tyre_type": 0,
        "safety_car": False,
        "traffic": RaceEnvironment.TRAFFIC_HIGH,
        "deg_rate": 1.5
    }
}

def run_phase(task_id, agent, episodes=5, seed=42):
    env = RaceEnvironment(max_laps=30)
    scenario = PHASE_SCENARIOS.get(task_id, {})
    
    total_score = 0.0
    breakdown_per_lap = []
    
    # We use the hard agent as an oracle to evaluate optimal actions
    oracle = HardMultiFactorAgent()
    
    for ep in range(episodes):
        obs = env.reset(scenario)
        if hasattr(agent, "reset"):
            agent.reset()
            
        ep_score = 0.0
        while not env.done:
            action = agent.select_action(obs)
            optimal_action = oracle._get_optimal(obs)
            
            obs, reward, done, info = env.step(action, optimal_action=optimal_action)
            ep_score += reward
            breakdown_per_lap.append({
                "lap": env.lap - 1,
                "action": action,
                "reward": reward,
                "breakdown": info.get("reward_breakdown", {})
            })
            
        total_score += (ep_score / env.steps_in_ep) if env.steps_in_ep > 0 else 0
        
    avg_score = total_score / episodes
    
    result = {
        "score": round(avg_score, 4),
        "breakdown_per_lap": breakdown_per_lap,
        "avg_reward": round(avg_score, 4),
        "episodes_run": episodes
    }
    
    return result
