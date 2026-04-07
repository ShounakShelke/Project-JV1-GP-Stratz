from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional

class ActionRequest(BaseModel):
    action: int = Field(..., description="Action index (0-4)")

class RaceState(BaseModel):
    lap_number: int
    tyre_wear: float
    weather: int
    gap_to_car: float
    safety_car: bool
    traffic_level: int
    tyre_deg_rate: float
    tyre_type: int

class ResetResponse(BaseModel):
    status: str = "ready"
    env: str = "GP-Stratz"
    description: str = "Motorsport Strategy Selection Environment"
    tasks: List[str] = ["easy", "medium", "hard"]
    actions: Dict[str, str]
    state: RaceState

class StepResponse(BaseModel):
    state: RaceState
    reward: float
    done: bool
    info: Dict[str, Any]

class StateResponse(BaseModel):
    state: RaceState

class BenchmarkResponse(BaseModel):
    env: str = "GP-Stratz"
    accuracy: str
    score: float
    tasks: Dict[str, float]
    status: str
    note: str
