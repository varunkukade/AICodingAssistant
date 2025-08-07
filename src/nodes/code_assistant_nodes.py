from src.llm_providers.groq import GroqProvider
from src.models.strategic_planner_output import StrategicPlannerOutput
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
from langgraph.runtime import Runtime
from src.llm_providers.openai import OpenAIProvider
from src.context_schema.code_assistant_context_schema import CodeAssistantContextSchema
class CodeAssistantNodes:
    def __init__(self):
        self.code_assistant_chains = CodeAssistantChains()
        self.llm = None

    def prepare_llm(self, state: CodeAssistantState, runtime: Runtime[CodeAssistantContextSchema]):
        requested_llm = getattr(runtime, "context", {}).get("model_provider", "")
        requested_model = getattr(runtime, "context", {}).get("model_name", "")
        if requested_llm == "openai":
            self.llm = OpenAIProvider(model_name=requested_model).get_llm()
        elif requested_llm == "groq":
            self.llm = GroqProvider(model_name=requested_model).get_llm()
    
    def strategic_planner(self, state: CodeAssistantState):
        print("Inside Strategic Planner")
        strategic_planner_chain = (
            self.code_assistant_chains.create_strategic_planner_chain(self.llm)
        )
        is_replanning_needed = bool(state.ambiguous_files) or bool(state.decision) or bool(state.additional_query)
        is_ambiguous = True if state.ambiguous_files else False
        decision = "Changed Accepted" if state.decision == "accept" else "Changed Rejected" if state.decision == "reject" else "No Decision yet"
        strategic_planner_output: StrategicPlannerOutput = strategic_planner_chain.invoke(
            {
                "messages": state.messages,
                "is_replanning_needed": is_replanning_needed,
                "step_number_to_replan_from": state.current_step_index + 1,
                "execution_plan": state.execution_plan or "No Execution Plan created yet.",
                "is_ambiguous": is_ambiguous,
                "decision": decision,
            }
        )
        print("Strategic Planner Plan: ", strategic_planner_output.plan)
        return {
            "execution_plan": strategic_planner_output.plan,
        }
    
    def task_executor(self, state: CodeAssistantState):
        # execute the step and update the state
        print("Inside Task executor")
        if not state.execution_plan:
            return Command(
                        goto="workflow_terminated",
                        update={
                            "summary": 'Workflow Terminated due to some unexpected error',
                            "files": None,
                            "current_step_index": 0,
                            "execution_plan": [],
                            "completed_tasks": [],
                            "step_executed": None,
                            "file_path_confirmation_prompt": None,
                            "human_feedback": None,
                            "decision": None,
                            "ambiguous_files": [],
                        },
                    )        
        task = state.execution_plan[state.current_step_index]
        print("Current Task: ", task)
        print('\n')
        is_replanning_needed = False
        should_terminate = False
        summary = ''
        files = None
        new_step_index = state.current_step_index
        step_executed = state.step_executed
        are_steps_completed = False
        file_path_confirmation_prompt = None
        human_feedback = None
        ambiguous_files = []
        messages = []
        decision = None
        additional_query = None
        if task == "decode_files":
            result = self.decode_files(state)
            is_replanning_needed = result.get("is_replanning_needed", False)
            should_terminate = result.get("should_terminate", False)
            summary = result.get("summary", '')
            files = result.get("files", None)
            ambiguous_files = result.get("ambiguous_files", [])
            new_step_index = new_step_index + 1
            are_steps_completed = new_step_index == len(state.execution_plan)
        if task == "resolve_ambiguity":
            result = self.resolve_ambiguity(state)
            is_replanning_needed = result.get("is_replanning_needed", False)
            should_terminate = result.get("should_terminate", False)
            summary = result.get("summary", '')
            files = result.get("files", state.files)
            file_path_confirmation_prompt = result.get("file_path_confirmation_prompt", None)
            human_feedback = result.get("human_feedback", None)
            new_step_index = new_step_index + 1
            are_steps_completed = new_step_index == len(state.execution_plan)
        if task == "analyse_feedback":
            result = self.analyse_feedback(state)
            is_replanning_needed = result.get("is_replanning_needed", False)
            should_terminate = result.get("should_terminate", False)
            summary = result.get("summary", '')
            files = result.get("files", state.files)
            messages = result.get("messages", state.messages)
            additional_query = result.get("additional_query", None)
            new_step_index = new_step_index + 1
            are_steps_completed = new_step_index == len(state.execution_plan)
        if task == "fetch_files":
            result = self.fetch_files(state)
            is_replanning_needed = result.get("is_replanning_needed", False)
            should_terminate = result.get("should_terminate", False)
            summary = result.get("summary", '')
            files = result.get("files", state.files)
            new_step_index = new_step_index + 1
            are_steps_completed = new_step_index == len(state.execution_plan)
        if task == "llm_call":
            result = self.llm_call(state)
            is_replanning_needed = result.get("is_replanning_needed", False)
            should_terminate = result.get("should_terminate", False)
            summary = result.get("summary", '')
            files = result.get("files", state.files)
            new_step_index = new_step_index + 1
            are_steps_completed = new_step_index == len(state.execution_plan)
        if task == "update_file":
            result = self.update_file(state)
            is_replanning_needed = result.get("is_replanning_needed", False)
            should_terminate = result.get("should_terminate", False)
            summary = result.get("summary", state.summary)
            files = result.get("files", state.files)
            new_step_index = new_step_index + 1
            are_steps_completed = new_step_index == len(state.execution_plan)
        if task == "human_approval":
            result = self.human_approval(state)
            is_replanning_needed = result.get("is_replanning_needed", False)
            should_terminate = result.get("should_terminate", False)
            summary = result.get("summary", '')
            files = result.get("files", state.files)
            decision = result.get("decision", None)
            new_step_index = new_step_index + 1
            are_steps_completed = new_step_index == len(state.execution_plan)
        if task == "approved_path": 
            result = self.approved_path(state)
            is_replanning_needed = result.get("is_replanning_needed", False)
            should_terminate = result.get("should_terminate", False)
            summary = result.get("summary", '')
            new_step_index = new_step_index + 1
            are_steps_completed = new_step_index == len(state.execution_plan)
        if task == "rejected_path": 
            result = self.rejected_path(state)
            is_replanning_needed = result.get("is_replanning_needed", False)
            should_terminate = result.get("should_terminate", False)
            files = result.get("files", state.files)
            summary = result.get("summary", '')
            new_step_index = new_step_index + 1
            are_steps_completed = new_step_index == len(state.execution_plan)

        step_executed = task    
        print("Finished Task: ", task)
        print("Is replanning needed: ", is_replanning_needed)
        print("New step index: ", new_step_index)
        print("Are steps completed: ", are_steps_completed)
        print("Should terminate: ", should_terminate)
        print("Summary: ", summary)
        print("Files: ", files)
        print("File path confirmation prompt: ", file_path_confirmation_prompt)
        print("Human feedback: ", human_feedback)
        print("Decision: ", decision)
        
        print('\n')

        if is_replanning_needed:
            return Command(
                goto="strategic_planner",
                update={
                    "summary": summary,
                    "ambiguous_files": ambiguous_files,
                    "current_step_index": new_step_index,
                    "messages": messages,
                    "decision": decision,
                    "step_executed": step_executed,
                    "files": files,
                    "additional_query": additional_query,
                },
            )
        else:
            if are_steps_completed:
                return Command(
                    goto="workflow_completed",
                    update={
                        "summary": summary,
                        "files": [],
                        "current_step_index": 0,
                        "execution_plan": [],
                        "completed_tasks": [],
                        "step_executed": step_executed,
                    },
                )
            else:
                if should_terminate:
                    return Command(
                        goto="workflow_terminated",
                        update={
                            "summary": summary,
                            "files": None,
                            "current_step_index": 0,
                            "execution_plan": [],
                            "completed_tasks": [],
                            "step_executed": step_executed,
                        },
                    )
                else:
                    return Command(
                        goto="task_executor",
                        update={
                            "current_step_index": new_step_index,
                            "summary": summary,
                            "files": files,
                            "file_path_confirmation_prompt": file_path_confirmation_prompt,
                            "human_feedback": human_feedback,
                            "step_executed": step_executed,
                        },
                    )

    def workflow_completed(self, state: CodeAssistantState):
        print("Workflow completed")

    def workflow_terminated(self, state: CodeAssistantState):
        print("Workflow terminated")

    def decode_files(self, state: CodeAssistantState):
        if state.files:
            formatted_files = format_files_for_prompt(state.files)
        else:
            formatted_files = []        
        decode_file_name_chain = (
            self.code_assistant_chains.create_decode_file_name_chain(self.llm)
        )
        decoded_files: DecodeFileNameOutput = decode_file_name_chain.invoke(
            {
                "messages": state.messages,
                "formatted_files": formatted_files or "No Existing Files Found.",
            }
        )
        # Initialize list to store ambiguous files
        ambiguous_files = []

        # Check for ambiguous files
        for file in decoded_files.files:
            if not file.file_name:
                continue
            result = check_file_ambiguity(file)
            if result.get("is_ambiguous", True) or result.get("is_ambigious_and_invalid_file_path", True):
                user_provided_path = (
                    file.file_path if result.get("is_ambigious_and_invalid_file_path", False) else None
                )
                ambiguous_files.append((file.file_name, result.get("valid_paths", []), user_provided_path))

        if decoded_files.should_end:
            return {
                "should_terminate": True,
                "is_replanning_needed": False,
                "summary": decoded_files.summary,
            }
        if ambiguous_files:
            return {
                "should_terminate": False,
                "is_replanning_needed": True,
                "ambiguous_files": ambiguous_files,
                "files": decoded_files.files,
            }
        return {
            "should_terminate": False,
            "is_replanning_needed": False,
            "summary": decoded_files.summary,
            "files": decoded_files.files,
        }

    def resolve_ambiguity(self, state: CodeAssistantState):
        # If there are ambiguous files, prompt the user
        file_path_confirmation_prompt = contruct_file_path_confirmation_prompt(
            state.ambiguous_files
        )
        feedback = interrupt(
            {
                "question": file_path_confirmation_prompt,
                "from": "human_feedback",
            }
        )
        return {
            "should_terminate": False,
            "is_replanning_needed": False,
            "summary": "\nPlease wait a moment, I am analysing your feedback...\n",
            "file_path_confirmation_prompt": file_path_confirmation_prompt,
            "human_feedback": feedback,
        }

    def analyse_feedback(self, state: CodeAssistantState):
        formatted_files = format_files_for_prompt(state.files)
        analyse_feedback_chain = (
            self.code_assistant_chains.create_analyse_feedback_chain(self.llm)
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
            return {
                "should_terminate": True,
                "is_replanning_needed": False,
                "summary": analyse_human_feedback_output.summary,
            }
        if analyse_human_feedback_output.additional_query:
            return {
                "should_terminate": False,
                "is_replanning_needed": True,
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
                "additional_query": analyse_human_feedback_output.additional_query,
            }
        return {
            "should_terminate": False,
            "is_replanning_needed": False,
            "files": analyse_human_feedback_output.files,
            "summary": "Thanks for confirming the file paths. Let me fetch those files...",
        }

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
            val = len(found_files) > 1 and "s" or ""
            summary_parts.append(
                f"I found the file{val} - {', '.join(found_files)}."
            )
            summary_parts.append(
                f"Please wait a moment.. Let me analyse the file{val}."
            )

        if missing_files:
            summary_parts.append(
                f"I couldn't find these file{len(missing_files) > 1 and 's' or ''} - {', '.join(missing_files)}."
            )
        
        summary = "\n".join(summary_parts)
        return {
            "is_replanning_needed": False,
            "should_terminate": False,
            "files": state.files, 
            "summary": summary
        }

    def llm_call(self, state: CodeAssistantState):
        formatted_files = format_files_for_prompt(state.files)
        analyse_update_chain = self.code_assistant_chains.create_analyse_update_chain(self.llm)
        llm_output: LLMAnalyseEditOutput = analyse_update_chain.invoke(
            {
                "messages": state.messages,
                "formatted_files": formatted_files,
            }
        )
        return {
            "is_replanning_needed": False,
            "should_terminate": False,
            "files": llm_output.files,
            "summary": llm_output.summary,
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
        print('\n')
        print("States history: ", states_history)  
        print('\n')
        # Get the state of graph before llm call and after update file
        state_before_llm_call: StateSnapshot | None = None
        state_after_llm_call: StateSnapshot | None = None
        if states_history:
            for each_state in states_history:
                if getattr(each_state, "values", None).get("step_executed", "") == "fetch_files":
                    state_before_llm_call = each_state
                if getattr(each_state, "values", None).get("step_executed", "") == "llm_call":
                    state_after_llm_call = each_state
        # Get the final list of files with their original content to reverse the changes in case of rejection
        files_to_reverse = get_files_to_reverse(
            getattr(state_before_llm_call, "values", None).get("files", None), 
            getattr(state_after_llm_call, "values", None).get("files", None)
        )
        print("\n")
        print("Files to reverse: ", files_to_reverse)
        print("\n")
        return {
                "is_replanning_needed": True,
                "should_terminate": False,
                "files": state.files if decision == "accept" else files_to_reverse,
                "decision": decision,
                "summary": ""
            }

    def approved_path(self, state: CodeAssistantState):
        return {
            "is_replanning_needed": False,
            "should_terminate": False,
            "summary": "Successfully updated the files.",
        }

    def rejected_path(self, state: CodeAssistantState):
        # reverse the files to its original state
        print('\n')
        print("Inside Rejected Path", state.files)
        print('\n')
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
            "is_replanning_needed": False,
            "should_terminate": False,
            "summary": "Successfully reversed the changes.",
        }
