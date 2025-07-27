from typing import List, Optional
from src.models.file import File
from pathlib import Path
import pathspec
import os

project_root = Path(os.getcwd())

def format_files_for_prompt(files: List[File]) -> str:
    return "\n".join(
        f"Filename: {file.file_name}\nDoes file exist: {file.exists}\nFile Path: {file.file_path}\nFile Content:\n```python\n{file.content}\n```"
        for file in files
    )

def get_gitignore_spec():
    # Generate gitignore path
    gitignore_path = project_root / ".gitignore"

    # Load gitignore rules
    if gitignore_path.exists():
        with open(gitignore_path, "r") as f:
            lines = f.readlines()
            spec = pathspec.PathSpec.from_lines("gitwildmatch", lines)
    else:
        spec = pathspec.PathSpec.from_lines("gitwildmatch", [])
    return spec

def get_valid_file_paths(paths_found: List[Path]) -> List[Path]:
    valid_paths = []
    spec = get_gitignore_spec()
    for p in paths_found:
        # Convert to relative path
        relative_path = p.relative_to(project_root).as_posix()
        # If the path is NOT in gitignore, keep it
        if not spec.match_file(relative_path):
            valid_paths.append(p)
    return valid_paths

def check_file_ambiguity(file: File) -> dict:
    # Get all matching paths in the project
    paths_found = list(project_root.rglob(file.file_name))
    # Now filter out the paths that are in gitignore
    valid_paths = get_valid_file_paths(paths_found)

    # There are two scenarios here:
    # 1. file.file_path is None and there are multiple valid paths for certain file name. 
    # 2. file.file_path is present, there are multiple valid paths for certain file name and file.file_path is not one of them - this means user provided file path doesn't exist/is invalid for that file.
    # example: Valid paths: [PosixPath('/Users/vkukade/Documents/AgenticAI/AICodeAssistant/models/index.py'), PosixPath('/Users/vkukade/Documents/AgenticAI/AICodeAssistant/prompt_template/index.py')]
    # Wrong File path : /Users/vkukade/Documents/AgenticAI/AICodeAssistant/index.py
    # In this case we should inform user that your provided file path is invalid.
    is_ambiguous = bool(valid_paths) and len(valid_paths) > 1 and file.file_path == ""
    is_ambigious_and_invalid_file_path = bool(valid_paths) and len(valid_paths) > 1 and file.file_path and Path(file.file_path) not in valid_paths
    return {
        "is_ambiguous": is_ambiguous,
        "is_ambigious_and_invalid_file_path": is_ambigious_and_invalid_file_path,
        "valid_paths": valid_paths,
    }

def contruct_file_path_confirmation_prompt(
    ambiguous_files: List[tuple[str, List[Path], Optional[str]]]
) -> str:
    file_path_confirmation_prompt = ""

    for file_name, paths, user_provided_path in ambiguous_files:
        if user_provided_path:  # case when user provided an invalid path
            file_path_confirmation_prompt += (
                f"⚠️ Your provided file path `{user_provided_path}` for file "
                f"**{file_name}** was invalid. I found possible correct paths:\n"
            )
        else:
            file_path_confirmation_prompt += f"🔸 **{file_name}** has multiple matches:\n"

        for path in paths:
            file_path_confirmation_prompt += f"   - {path}\n"

        file_path_confirmation_prompt += "\n"

    file_path_confirmation_prompt += (
        "👉 Please specify the correct paths for each above file and also let me know if you have any additional queries.\n"
    )

    return file_path_confirmation_prompt
