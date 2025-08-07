from typing import Literal, Optional, Annotated, List, Tuple
from langchain_core.messages.base import BaseMessage

from langgraph.graph import add_messages
from src.models.file import File
from pydantic import BaseModel
from pathlib import Path

class CodeAssistantState(BaseModel):
    messages: Annotated[List[BaseMessage], add_messages]
    files: Optional[List[File]] = None
    summary: Optional[str] = None
    human_feedback: Optional[str] = None
    file_path_confirmation_prompt: Optional[str] = None

    # Needed to decide whether to replan or not
    ambiguous_files: List[Tuple[str, List[Path], Optional[str]]] = []
    decision: Optional[Literal["accept", "reject"]] = None
    additional_query: Optional[str] = None

    # Planning & Execution
    execution_plan: List[str] = []           # Current list of planned steps
    current_step_index: int = 0              # Which step to execute next
    step_executed: Optional[str] = None      # Step that was executed
