from pydantic import BaseModel
from typing import List
from src.models.file import File


class DecodeFileNameOutput(BaseModel):
    files: List[File]
    should_end: bool
    summary: str
