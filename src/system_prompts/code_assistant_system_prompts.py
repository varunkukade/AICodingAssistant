from src.system_prompts.decode_system_prompt import decode_system_prompt
from src.system_prompts.analyse_feedback_system_prompt import (
    analyse_feedback_system_prompt,
)
from src.system_prompts.analyse_update_system_prompt import analyse_update_system_prompt

class CodeAssistantSystemPrompts:
    def fetch_decode_system_prompt(self):
        return decode_system_prompt

    def fetch_analyse_feedback_system_prompt(self):
        return analyse_feedback_system_prompt

    def fetch_analyse_update_system_prompt(self):
        return analyse_update_system_prompt
