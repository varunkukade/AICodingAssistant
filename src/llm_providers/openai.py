from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from src.utils.api_key import get_api_key


class OpenAIProvider:
    def __init__(self, model_name: str):
        # Load environment variables
        load_dotenv()
        self.model_name = model_name

    def get_llm(self):
        try:
            get_api_key("OPENAI_API_KEY", "Enter API key for OpenAI: ")

            if not self.model_name:
                raise ValueError("Model name is not provided")

            llm = ChatOpenAI(
                model=self.model_name,
                temperature=0,
                max_tokens=None,
                timeout=None,
                max_retries=2,
            )
            return llm
        except Exception as e:
            raise ValueError(f"Error occurred with exception : {e}")
