from src.llm_providers.openai import OpenAIProvider
from langchain_core.messages import HumanMessage
from src.graphs.graph_builder import GraphBuilder
from src.utils.logging import log_data
from langgraph.types import Command
from src.utils.graph import handle_interrupt
import os
from dotenv import load_dotenv
import questionary

# Load environment variables
load_dotenv()

os.environ["LANGCHAIN_TRACING_V2"] = "true"

graph_builder = GraphBuilder()
graph = graph_builder.compile_graph()

def run_request(user_input: str, model_provider: str, model_name: str):
    messages = [HumanMessage(content=user_input)]
    request = {"messages": messages}
    config = {"configurable": {"thread_id": "1", "user_id": "1"}}
    sections = [
        "decode_files",
        "human_feedback",
        "analyse_feedback",
        "fetch_files",
        "llm_call",
        "approved_path",
        "rejected_path",
    ]

    for chunk in graph.stream(
        request,
        config=config,
        stream_mode="updates",
        context={
            "model_provider": model_provider,
            "model_name": model_name,
        },
    ):
        log_data(chunk, sections)
        resume = handle_interrupt(graph, config, chunk)
        if resume:
            for chunk in graph.stream(
                Command(resume=resume),
                config=config,
                stream_mode="updates",
                context={
                    "model_provider": model_provider,
                    "model_name": model_name,
                },
            ):
                log_data(chunk, sections)
                resume = handle_interrupt(graph, config, chunk)
                if resume:
                    graph.invoke(
                        Command(resume=resume),
                        config=config,
                    )
    
if __name__ == "__main__":
    # Analyse file
    # messages = [HumanMessage(content="Can you analyse the code in refactor.py?")]

    # Refactor file and llm create new file on its own.
    # messages = [HumanMessage(content="Can you refactor the code in refactor.py and add tests for it?")]
    # messages = [HumanMessage(content="Can you add subtraction code inside test.py")]
    # messages = [HumanMessage(content="Can you analyse the code in test.py?")]
    model_provider = questionary.select(
        "Which provider do you want to use?",
        choices=["openai", "groq"]
    ).ask()
    print("\n") 
    if model_provider.lower().strip() == "openai":
        model_name = questionary.select(
            "Select OpenAI model name: ",
            choices=["gpt-3.5-turbo", "gpt-4o", "gpt-4o-mini", "gpt-4.1"]
        ).ask()
    elif model_provider.lower().strip() == "groq":
        model_name = questionary.select(
            "Select Groq model name: ",
            choices=["", "qwen/qwen3-32b"]
        ).ask()
    else:
        raise ValueError("Invalid model provider")
    print("\n")
    user_input = questionary.text("Enter your query: ").ask()
    print("\n") 
    run_request(user_input, model_provider, model_name)
