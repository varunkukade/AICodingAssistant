from dataclasses import dataclass

@dataclass
class CodeAssistantContextSchema:
    model_provider: str = "openai"
    model_name: str = "gpt-4o"