from typing import Optional
from typing import Annotated, Optional, List
from langchain_core.messages.base import BaseMessage

from langgraph.graph import add_messages
from src.models.file import File
from pydantic import BaseModel


class CodeAssistantState(BaseModel):
    messages: Annotated[List[BaseMessage], add_messages]
    files: Optional[List[File]] = None
    summary: Optional[str] = None
    human_feedback: Optional[str] = None
    file_path_confirmation_prompt: Optional[str] = None
