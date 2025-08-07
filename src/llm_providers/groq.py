from src.utils.api_key import get_api_key
from langchain_groq import ChatGroq

class GroqProvider:
    def __init__(self, model_name: str):
        self.model_name = model_name

    def get_llm(self):
        try:
            get_api_key("GROQ_API_KEY", "Enter API key for Groq: ")

            if not self.model_name:
                raise ValueError("Model name is not provided")

            llm = ChatGroq(
                model=self.model_name,
                temperature=0,
                max_tokens=None,
                timeout=None,
                max_retries=2,
            )
            return llm
        except Exception as e:
            raise ValueError(f"Error occurred while initializing Groq : {e}")
