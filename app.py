import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from env.race_env import RaceEnvironment
from agents import AGENT_REGISTRY, AGENT_META
from graders.phase_grader import run_phase, PHASE_SCENARIOS

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TASKS = [
    {"id": "easy", "task_id": "easy", "grader": "deterministic"},
    {"id": "medium", "task_id": "medium", "grader": "deterministic"},
    {"id": "hard", "task_id": "hard", "grader": "deterministic"},
]

global_env = RaceEnvironment(max_laps=30)

@app.get("/")
def root():
    index_path = os.path.join(os.path.dirname(__file__), "frontend", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "GP-Stratz running, but frontend/index.html not found"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/metadata")
def metadata():
    return {"name": "gp-stratz", "description": "GP-Stratz running"}

@app.get("/schema")
def schema():
    return {
        "action": {
            "type": "integer",
            "description": "0=PIT, 1=STAY, 2=CONSERVE, 3=PUSH, 4=SWAP"
        },
        "observation": {
            "type": "object",
            "properties": {
                "lap_number": {"type": "integer"},
                "tyre_wear": {"type": "number"},
                "weather": {"type": "integer"},
                "gap_to_car": {"type": "number"},
                "safety_car": {"type": "boolean"},
                "traffic_level": {"type": "integer"},
                "tyre_deg_rate": {"type": "number"},
                "tyre_type": {"type": "integer"}
            }
        },
        "state": {"type": "object", "properties": {}}
    }

@app.get("/agents")
def list_agents():
    return [
        {
            "id": k,
            **v
        } for k, v in AGENT_META.items()
    ]

@app.get("/tasks")
def list_tasks():
    return TASKS

@app.get("/tasks/{task_id}/grade")
def grade_task(task_id: str):
    if task_id not in PHASE_SCENARIOS:
        raise HTTPException(status_code=404, detail="Unknown task")
    
    agent_id = task_id if task_id in AGENT_REGISTRY else "hard"
    agent = AGENT_REGISTRY[agent_id]()
    result = run_phase(task_id, agent)
    return {"task_id": task_id, "score": result["score"], "breakdown": result["breakdown_per_lap"]}

class ResetRequest(BaseModel):
    task_id: str = "easy"

@app.post("/reset")
async def reset(req: Optional[ResetRequest] = None):
    task_id = req.task_id if req else "easy"
    scenario = PHASE_SCENARIOS.get(task_id, {})
    obs = global_env.reset(scenario)
    return {"state": obs, "actions": {"0": "PIT", "1": "STAY", "2": "CONSERVE", "3": "PUSH", "4": "SWAP"}}

class StepRequest(BaseModel):
    action: int

@app.post("/step")
async def step(req: StepRequest):
    from agents.hard_agent import HardMultiFactorAgent
    oracle = HardMultiFactorAgent()
    optimal_action = oracle._get_optimal(global_env.state())
    obs, reward, done, info = global_env.step(req.action, optimal_action=optimal_action)
    return {"state": obs, "reward": reward, "done": done, "info": info}

class RunAgentRequest(BaseModel):
    task_id: str

@app.post("/agents/{agent_id}/run")
async def run_agent_on_phase(agent_id: str, req: RunAgentRequest):
    if agent_id not in AGENT_REGISTRY:
        raise HTTPException(status_code=404, detail="Unknown agent")
    if req.task_id not in PHASE_SCENARIOS:
        raise HTTPException(status_code=404, detail="Unknown task")
        
    agent = AGENT_REGISTRY[agent_id]()
    result = run_phase(req.task_id, agent, episodes=1)
    return result

def main():
    import uvicorn
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
