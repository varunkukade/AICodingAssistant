from src.utils.file import format_files_for_prompt
from src.states.code_assistant_state import CodeAssistantState
from src.chains.code_assistant_chains import CodeAssistantChains
from langgraph.types import StateSnapshot, interrupt, Command
from src.utils.file import check_file_ambiguity, contruct_file_path_confirmation_prompt
from langchain_core.messages import AIMessage, HumanMessage
from pathlib import Path
from src.utils.file import project_root, get_valid_file_paths
from src.models.llm_analyse_edit_output import LLMAnalyseEditOutput
from src.models.decode_file_name import DecodeFileNameOutput
from src.models.analyse_human_feedback import AnalyseHumanFeedbackOutput
from src.utils.graph import get_files_to_reverse


class CodeAssistantNodes:
    def __init__(self, llm):
        self.llm = llm
        self.code_assistant_chains = CodeAssistantChains(llm)

    def decode_files(self, state: CodeAssistantState):
        if state.files:
            formatted_files = format_files_for_prompt(state.files)
        else:
            formatted_files = []
        decode_file_name_chain = (
            self.code_assistant_chains.create_decode_file_name_chain()
        )
        decoded_files: DecodeFileNameOutput = decode_file_name_chain.invoke(
            {
                "messages": state.messages,
                "formatted_files": formatted_files or "No Existing Files Found.",
            }
        )
        if decoded_files.should_end:
            return Command(
                goto="__end__",
                update={
                    "summary": decoded_files.summary,
                },
            )
        return Command(
            goto="human_feedback",
            update={
                "files": decoded_files.files,
                "summary": decoded_files.summary,
            },
        )

    def human_feedback(self, state: CodeAssistantState):
        # Initialize list to store ambiguous files
        ambiguous_files = []

        # Check for ambiguous files
        for file in state.files:
            if not file.file_name:
                continue
            result = check_file_ambiguity(file)
            if result.get("is_ambiguous", False):
                ambiguous_files.append((file.file_name, result.get("valid_paths", [])))

        # If there are ambiguous files, prompt the user
        if ambiguous_files:
            file_path_confirmation_prompt = contruct_file_path_confirmation_prompt(
                ambiguous_files
            )
            feedback = interrupt(
                {"question": file_path_confirmation_prompt, "from": "human_feedback"}
            )
            return Command(
                update={
                    "file_path_confirmation_prompt": file_path_confirmation_prompt,
                    "human_feedback": feedback,
                    "summary": "\nPlease wait a moment, I am analysing your feedback...\n",
                }
            )
        else:
            return Command(
                update={
                    "file_path_confirmation_prompt": None,
                    "human_feedback": None,
                }
            )

    def analyse_feedback(self, state: CodeAssistantState):
        formatted_files = format_files_for_prompt(state.files)
        analyse_feedback_chain = (
            self.code_assistant_chains.create_analyse_feedback_chain()
        )
        analyse_human_feedback_output: AnalyseHumanFeedbackOutput = (
            analyse_feedback_chain.invoke(
                {
                    "formatted_files": formatted_files,
                    "human_feedback": state.human_feedback,
                    "file_path_confirmation_prompt": state.file_path_confirmation_prompt,
                }
            )
        )
        if analyse_human_feedback_output.should_end:
            return Command(
                goto="__end__",
                update={
                    "summary": analyse_human_feedback_output.summary,
                },
            )
        if analyse_human_feedback_output.additional_query:
            return Command(
                goto="decode_files",
                update={
                    "files": analyse_human_feedback_output.files,
                    "messages": [
                        AIMessage(
                            content="Do you have any other queries in addition to the above? I can process all of them simultaneously."
                        ),
                        HumanMessage(
                            content=analyse_human_feedback_output.additional_query
                        ),
                    ],
                    "summary": "Thanks for confirming the file paths. Now let me analyse your additional queries.",
                },
            )
        return Command(
            goto="fetch_files",
            update={
                "files": analyse_human_feedback_output.files,
                "summary": "Thanks for confirming the file paths. Let me fetch those files...",
            },
        )

    def fetch_files(self, state: CodeAssistantState):
        for file in state.files:
            if not file.file_name:
                continue
            if file.file_path:
                print(f"✅ File path confirmed by user: {file.file_path}")
                # file path already confirmed by user
                resolved_path = Path(file.file_path)
                relative_path = resolved_path.relative_to(project_root)
                file.file_path = str(relative_path)
                file.content = resolved_path.read_text(encoding="utf-8")
                file.exists = True
            else:
                # either file doesn't exist or each file has only one path
                # Get all matching paths in the project
                paths_found = list(project_root.rglob(file.file_name))

                # Now filter out the paths that are in gitignore
                valid_paths = get_valid_file_paths(paths_found)
                if valid_paths:
                    # if valid paths found, use first match as there is only one valid path
                    resolved_path = valid_paths[0]
                    relative_path = resolved_path.relative_to(project_root)
                    file.file_path = str(relative_path)
                    file.content = resolved_path.read_text(encoding="utf-8")
                    file.exists = True
                else:
                    # if no valid paths found, file doesn't exist
                    file.file_path = ""
                    file.content = ""
                    file.exists = False

        found_files = [file.file_name for file in state.files if file.exists]
        missing_files = [file.file_name for file in state.files if not file.exists]
        summary_parts = []

        if found_files:
            summary_parts.append(
                f"I found these file{len(found_files) > 1 and 's' or ''} - {', '.join(found_files)}."
            )

        if missing_files:
            summary_parts.append(
                f"I couldn't find these file{len(missing_files) > 1 and 's' or ''} - {', '.join(missing_files)}."
            )

        summary = "\n".join(summary_parts)
        return {"files": state.files, "summary": summary}

    def llm_call(self, state: CodeAssistantState):
        formatted_files = format_files_for_prompt(state.files)
        analyse_update_chain = self.code_assistant_chains.create_analyse_update_chain()
        llm_output: LLMAnalyseEditOutput = analyse_update_chain.invoke(
            {
                "messages": state.messages,
                "formatted_files": formatted_files,
            }
        )
        return {
            "files": llm_output.files,
            "summary": llm_output.summary,
            "is_update": llm_output.is_update,
        }

    def update_file(self, state: CodeAssistantState):
        for file in state.files:
            # Use file_path if available, otherwise fallback to root/file_name
            path = (
                Path(file.file_path) if file.file_path else Path(".") / file.file_name
            )
            # Ensure parent directories exist
            path.parent.mkdir(parents=True, exist_ok=True)
            # Write content
            path.write_text(file.content, encoding="utf-8")
        return {
            "files": state.files,
        }

    def human_approval(self, state: CodeAssistantState):
        interrupt_response: dict = interrupt(
            {
                "question": f"Here is the summary of changes \n {state.summary}\n Do you approve the output? Type 'accept' or 'reject':- ",
                "from": "human_approval",
            }
        )
        decision: str = interrupt_response.get("decision", "")
        states_history: list[StateSnapshot] = interrupt_response.get("state_history", [])

        # Get the state of graph before llm call and after update file
        state_before_llm_call: StateSnapshot | None = None
        state_after_llm_call: StateSnapshot | None = None
        if states_history:
            for each_state in states_history:
                if each_state.next and each_state.next[0] == "llm_call":
                    state_before_llm_call = each_state
                if each_state.next and each_state.next[0] == "update_file":
                    state_after_llm_call = each_state
        # Get the final list of files with their original content to reverse the changes in case of rejection
        files_to_reverse = get_files_to_reverse(
            state_before_llm_call.values["files"], state_after_llm_call.values["files"]
        )
        if decision == "accept":
            return Command(goto="approved_path", update={"decision": "accepted"})
        else:
            return Command(
                goto="rejected_path",
                update={"decision": "rejected", "files": files_to_reverse},
            )

    def approved_path(self, state: CodeAssistantState):
        return {
            "messages": state.messages,
            "summary": "Successfully updated the files.",
        }

    def rejected_path(self, state: CodeAssistantState):
        # reverse the files to its original state
        if state.files:
            for file in state.files:
                # Use file_path if available, otherwise fallback to root/file_name
                path = (
                    Path(file.file_path)
                    if file.file_path
                    else Path(".") / file.file_name
                )
                if file.exists:
                    # If the file exists, update it
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(file.content, encoding="utf-8")
                else:
                    # If the file was added newly, delete it now.
                    if path.exists() and path.is_file():
                        path.unlink()
        return {
            "messages": state.messages,
            "summary": "Successfully reversed the changes.",
        }
