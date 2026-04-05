import os
import sys

# Ensure current directory is in path for 'env' etc.
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.append(project_root)

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from env.race_env import RaceEnvironment

app = FastAPI(title="GP-Stratz Environment")
env = RaceEnvironment(max_laps=30)

class ActionRequest(BaseModel):
    action: int

@app.post("/reset")
def reset_env():
    state = env.reset()
    return {"state": state}

@app.post("/step")
def step_env(req: ActionRequest):
    if env.done:
        raise HTTPException(status_code=400, detail="Episode already finished. Call /reset")
    next_state, reward, done, info = env.step(req.action)
    return {
        "state": next_state,
        "reward": reward,
        "done": done,
        "info": info
    }

@app.get("/state")
def get_state():
    return {"state": env.state()}

def main():
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
