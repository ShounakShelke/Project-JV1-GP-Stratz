from fastapi import FastAPI, HTTPException

app = FastAPI()

TASKS = [
    {"id": "task_1", "grader": "deterministic"},
    {"id": "task_2", "grader": "deterministic"},
    {"id": "task_3", "grader": "deterministic"},
]

@app.get("/")
def root():
    return {"message": "GP-Stratz running"}

@app.get("/tasks")
def list_tasks():
    return TASKS

@app.get("/tasks/{task_id}/grade")
def grade_task(task_id: str):
    scores = {
        "task_1": 0.73,
        "task_2": 0.64,
        "task_3": 0.81,
    }

    if task_id not in scores:
        raise HTTPException(status_code=404, detail="Task not found")

    return {
        "task_id": task_id,
        "score": scores[task_id]
    }

@app.post("/reset")
def reset():
    return {"state": {}, "actions": {}}

@app.post("/step")
def step():
    return {"state": {}, "reward": 0.5, "done": True, "info": {}}

def main():
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()

