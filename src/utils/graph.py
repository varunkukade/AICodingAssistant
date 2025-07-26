from langgraph.graph.state import CompiledStateGraph
from src.models.file import File
from src.states.code_assistant_state import CodeAssistantState


def handle_interrupt(
    graph: CompiledStateGraph[CodeAssistantState], config: dict, chunk
):
    interrupt_response = chunk.get("__interrupt__", [])
    resume = None
    if (
        interrupt_response
        and len(interrupt_response) > 0
        and interrupt_response[0].value
        and interrupt_response[0].value.get("question")
        and interrupt_response[0].value.get("from")
    ):
        question = interrupt_response[0].value["question"]
        from_ = interrupt_response[0].value["from"]
        user_input = input(question)
        state_history = list(graph.get_state_history(config))
        if from_ == "human_approval":
            resume = {
                "decision": user_input.strip(),
                "state_history": state_history,
            }
        elif from_ == "human_feedback":
            resume = user_input.strip()
    return resume


def get_files_to_reverse(
    original_files: list[File], new_files: list[File]
) -> list[File]:
    final_files: list[File] = []
    # Add all old files to final list
    final_files.extend(original_files)
    # Create a set of (file_name, file_path) for quick lookup
    old_file_keys = set((f.file_name, f.file_path) for f in original_files)
    # Check for new files
    for file in new_files:
        key = (file.file_name, file.file_path)
        if key not in old_file_keys:
            # It's a new file, add it with empty content
            final_files.append(
                File(
                    file_name=file.file_name,
                    file_path=file.file_path,
                    content="",
                    exists=False,
                )
            )
    return final_files
