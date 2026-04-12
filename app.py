import os

from fastapi import FastAPI, HTTPException

app = FastAPI()

TASKS = [
    {"id": "easy", "task_id": "easy", "grader": "deterministic"},
    {"id": "medium", "task_id": "medium", "grader": "deterministic"},
    {"id": "hard", "task_id": "hard", "grader": "deterministic"},
]

SCORES = {
    "easy": 0.73,
    "medium": 0.64,
    "hard": 0.81,
}


@app.get("/")
def root():
    return {"message": "GP-Stratz running"}


@app.get("/health")
@app.get("/health/")
def health():
    return {"status": "healthy"}


@app.get("/metadata")
@app.get("/metadata/")
def metadata():
    return {"name": "gp-stratz", "description": "GP-Stratz running"}


@app.get("/schema")
@app.get("/schema/")
def schema():
    return {
        "action": {"type": "object", "properties": {}},
        "observation": {"type": "object", "properties": {}},
        "state": {"type": "object", "properties": {}},
    }


@app.get("/state")
@app.get("/state/")
def state():
    return {"state": {}}


@app.post("/mcp")
@app.post("/mcp/")
async def mcp(payload: dict):
    return {"jsonrpc": "2.0", "id": payload.get("id"), "result": {}}


@app.get("/tasks")
@app.get("/tasks/")
def list_tasks():
    return TASKS


@app.get("/tasks/{task_id}/grade")
@app.get("/tasks/{task_id}/grade/")
def grade_task(task_id: str):
    if task_id not in SCORES:
        raise HTTPException(status_code=404, detail="Unknown task")
    return {"task_id": task_id, "score": SCORES[task_id]}


@app.post("/reset")
@app.post("/reset/")
async def reset():
    return {"actions": {"0": "noop"}, "state": {}}


@app.post("/step")
@app.post("/step/")
async def step():
    return {"state": {}, "reward": 0.5, "done": True, "info": {}}


def main():
    import uvicorn

    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
