from src.prompts.decode_prompt import decode_prompt
from src.prompts.analyse_feedback_prompt import analyse_feedback_prompt
from src.prompts.analyse_update_prompt import analyse_update_prompt

class CodeAssistantPrompts:
    def fetch_decode_prompt(self):
        return decode_prompt

    def fetch_analyse_feedback_prompt(self):
        return analyse_feedback_prompt

    def fetch_analyse_update_prompt(self):
        return analyse_update_prompt
