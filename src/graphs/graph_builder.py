from langgraph.graph import END, START, StateGraph
from src.states.code_assistant_state import CodeAssistantState
from langgraph.checkpoint.memory import InMemorySaver
from src.nodes.code_assistant_nodes import CodeAssistantNodes
from src.context_schema.code_assistant_context_schema import CodeAssistantContextSchema
class GraphBuilder:
    def __init__(self):
        self.graph = StateGraph(CodeAssistantState, context=CodeAssistantContextSchema)

    def build_code_assistant_graph(self):
        code_assistant_nodes = CodeAssistantNodes()
        self.graph.add_node("prepare_llm", code_assistant_nodes.prepare_llm)
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
        self.graph.add_edge(START, "prepare_llm")
        self.graph.add_edge("prepare_llm", "decode_files")
        self.graph.add_edge("fetch_files", "llm_call")
        self.graph.add_edge("update_file", "human_approval")
        self.graph.add_edge("approved_path", END)
        self.graph.add_edge("rejected_path", END)

        return self.graph

    def compile_graph(self):
        self.build_code_assistant_graph()
        memory = InMemorySaver()
        graph = self.graph.compile(checkpointer=memory)
        return graph
