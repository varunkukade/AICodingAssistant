from src.llm_providers.openai import OpenAIProvider
from langchain_core.messages import HumanMessage
from src.graphs.graph_builder import GraphBuilder
from src.utils.logging import log_data
from langgraph.types import Command
from src.utils.graph import handle_interrupt
import os

os.environ["LANGCHAIN_TRACING_V2"] = "true"

if __name__ == "__main__":
    # Analyse file
    # messages = [HumanMessage(content="Can you analyse the code in refactor.py?")]

    # Refactor file and llm create new file on its own.
    # messages = [HumanMessage(content="Can you refactor the code in refactor.py and add tests for it?")]

    # Asks for human feedback after passing ambigious file paths input
    user_input = input("Enter your query: ")
    messages = [HumanMessage(content=user_input)]
    request = {
        "messages": messages,
    }
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
    llm = OpenAIProvider(model_name="gpt-4o").get_llm()
    graph_builder = GraphBuilder(llm)
    graph = graph_builder.compile_graph()
    for chunk in graph.stream(request, config=config, stream_mode="updates"):
        log_data(chunk, sections)
        resume = handle_interrupt(graph, config, chunk)
        if resume:
            for chunk in graph.stream(
                Command(resume=resume),
                config=config,
                stream_mode="updates",
            ):
                log_data(chunk, sections)
                resume = handle_interrupt(graph, config, chunk)
                if resume:
                    graph.invoke(
                        Command(resume=resume),
                        config=config,
                    )
