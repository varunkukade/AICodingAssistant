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
        self.graph.add_node("strategic_planner", code_assistant_nodes.strategic_planner)
        self.graph.add_node("task_executor", code_assistant_nodes.task_executor)
        self.graph.add_node("workflow_completed", code_assistant_nodes.workflow_completed)
        self.graph.add_node("workflow_terminated", code_assistant_nodes.workflow_terminated)

        # Add edges to the graph
        self.graph.add_edge(START, "prepare_llm")
        self.graph.add_edge("prepare_llm", "strategic_planner")
        self.graph.add_edge("strategic_planner", "task_executor")
        self.graph.add_edge("workflow_completed", END)
        self.graph.add_edge("workflow_terminated", END)

        return self.graph

    def compile_graph(self):
        self.build_code_assistant_graph()
        memory = InMemorySaver()
        graph = self.graph.compile(checkpointer=memory)
        return graph
