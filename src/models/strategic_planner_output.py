from pydantic import BaseModel
from typing import List

class StrategicPlannerOutput(BaseModel):
    """Output schema for strategic planner. Returns a list of tool names in sequence and summary also."""
    plan: List[str]