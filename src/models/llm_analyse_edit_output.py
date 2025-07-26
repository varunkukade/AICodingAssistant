from typing import List
from src.models.file import File
from pydantic import BaseModel


class LLMAnalyseEditOutput(BaseModel):
    files: List[File]
    summary: str
    is_update: bool
