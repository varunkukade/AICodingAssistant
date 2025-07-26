from langgraph.graph import END, START, StateGraph
from src.states.code_assistant_state import CodeAssistantState
from langgraph.checkpoint.memory import InMemorySaver
from src.nodes.code_assistant_nodes import CodeAssistantNodes


class GraphBuilder:
    def __init__(self, llm):
        self.graph = StateGraph(CodeAssistantState)
        self.llm = llm

    # Function to determine next node
    def __should_continue(self, state: CodeAssistantState) -> str:
        if state.is_update:
            return "update_file"
        return END

    def __go_to(self, state: CodeAssistantState) -> str:
        if state.human_feedback:
            return "analyse_feedback"
        return "fetch_files"

    def build_code_assistant_graph(self):
        code_assistant_nodes = CodeAssistantNodes(self.llm)
        self.graph.add_node("decode_files", code_assistant_nodes.decode_files)
        self.graph.add_node("human_feedback", code_assistant_nodes.human_feedback)
        self.graph.add_node("analyse_feedback", code_assistant_nodes.analyse_feedback)
        self.graph.add_node("fetch_files", code_assistant_nodes.fetch_files)
        self.graph.add_node("llm_call", code_assistant_nodes.llm_call)
        self.graph.add_node("update_file", code_assistant_nodes.update_file)
        self.graph.add_node("human_approval", code_assistant_nodes.human_approval)
        self.graph.add_node("approved_path", code_assistant_nodes.approved_path)
        self.graph.add_node("rejected_path", code_assistant_nodes.rejected_path)

        # Add edges to the graph
        self.graph.add_edge(START, "decode_files")

        self.graph.add_conditional_edges("human_feedback", self.__go_to)

        self.graph.add_edge("fetch_files", "llm_call")
        self.graph.add_conditional_edges(
            "llm_call",
            self.__should_continue,
        )
        self.graph.add_edge("update_file", "human_approval")
        self.graph.add_edge("approved_path", END)
        self.graph.add_edge("rejected_path", END)

        return self.graph

    def compile_graph(self):
        self.build_code_assistant_graph()
        memory = InMemorySaver()
        graph = self.graph.compile(checkpointer=memory)
        return graph
