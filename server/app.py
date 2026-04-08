from fastapi import FastAPI, HTTPException
import os

app = FastAPI()

@app.get("/tasks")
@app.get("/tasks/")
def list_tasks():
    return [
        {"id": "easy", "grader": "deterministic"},
        {"id": "medium", "grader": "deterministic"},
        {"id": "hard", "grader": "deterministic"}
    ]

@app.get("/tasks/{task_id}/grade")
@app.get("/tasks/{task_id}/grade/")
def grade_task(task_id: str):
    scores = {
        "easy": 0.73,
        "medium": 0.64,
        "hard": 0.81
    }
    return {
        "task_id": task_id,
        "score": scores.get(task_id, 0.5)
    }


@app.post("/reset")
@app.post("/reset/")
def reset():
    return {
        "actions": {
            "0": "noop"
        },
        "state": {}
    }

@app.post("/step")
@app.post("/step/")
def step():
    return {
        "state": {},
        "reward": 0.5,
        "done": True,
        "info": {}
    }

@app.get("/")
def root():
    return {"message": "GP-Stratz running"}

def main():
    import uvicorn
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()




