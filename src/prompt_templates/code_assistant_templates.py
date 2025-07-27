from typing import List
from langchain_core.prompts import ChatPromptTemplate
from src.prompts.code_assistant_prompts import CodeAssistantPrompts


class CodeAssistantTemplates:
    def __init__(self):
        self.code_assistant_prompts = CodeAssistantPrompts()

    def __fetch_decode_prompt(self):
        return self.code_assistant_prompts.fetch_decode_prompt()

    def __fetch_analyse_feedback_prompt(self):
        return self.code_assistant_prompts.fetch_analyse_feedback_prompt()

    def __fetch_analyse_update_prompt(self):
        return self.code_assistant_prompts.fetch_analyse_update_prompt()

    def __create_prompt_template(self, messages: List[tuple]) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages(messages)

    def get_decode_prompt_template(self):
        decode_prompt = self.__fetch_decode_prompt()
        return self.__create_prompt_template(decode_prompt)

    def get_analyse_feedback_prompt_template(self):
        analyse_feedback_prompt = self.__fetch_analyse_feedback_prompt()
        return self.__create_prompt_template(analyse_feedback_prompt)

    def get_analyse_update_prompt_template(self):
        analyse_update_prompt = self.__fetch_analyse_update_prompt()
        return self.__create_prompt_template(analyse_update_prompt)
