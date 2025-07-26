from pydantic import BaseModel
from typing import List
from src.models.file import File


class AnalyseHumanFeedbackOutput(BaseModel):
    files: List[File]
    additional_query: str
    should_end: bool
    summary: str
