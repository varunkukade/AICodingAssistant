from src.models.decode_file_name import DecodeFileNameOutput
from src.models.analyse_human_feedback import AnalyseHumanFeedbackOutput
from src.models.llm_analyse_edit_output import LLMAnalyseEditOutput
from src.prompt_templates.code_assistant_templates import CodeAssistantTemplates


class CodeAssistantChains:
    def __init__(self):
        self.code_assistant_templates = CodeAssistantTemplates()

    def create_decode_file_name_chain(self, llm):
        decode_prompt_template = (
            self.code_assistant_templates.get_decode_prompt_template()
        )
        return decode_prompt_template | llm.with_structured_output(
            DecodeFileNameOutput
        )

    def create_analyse_feedback_chain(self, llm):
        analyse_feedback_prompt_template = (
            self.code_assistant_templates.get_analyse_feedback_prompt_template()
        )
        return analyse_feedback_prompt_template | llm.with_structured_output(
            AnalyseHumanFeedbackOutput
        )

    def create_analyse_update_chain(self, llm):
        analyse_update_prompt_template = (
            self.code_assistant_templates.get_analyse_update_prompt_template()
        )
        return analyse_update_prompt_template | llm.with_structured_output(
            LLMAnalyseEditOutput
        )
