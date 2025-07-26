from typing import List
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

    # mark file as ambiguous only if:
    # 1. There are multiple valid paths and
    # 2. either file.file_path is None or file.file_path is not already one of them

    # Valid paths : [PosixPath('/Users/vkukade/Documents/AgenticAI/MiniCursor/models/index.py'), PosixPath('/Users/vkukade/Documents/AgenticAI/MiniCursor/prompt_template/index.py')]
    # File path : /Users/vkukade/Documents/AgenticAI/MiniCursor/prompt_template/index.py
    return {
        "is_ambiguous": bool(valid_paths)
        and len(valid_paths) > 1
        and (not file.file_path or Path(file.file_path) not in valid_paths),
        "valid_paths": valid_paths,
    }


def contruct_file_path_confirmation_prompt(
    ambiguous_files: List[tuple[str, List[Path]]]
) -> str:
    file_path_confirmation_prompt = (
        "The following files have multiple matching paths:\n"
    )
    for file_name, paths in ambiguous_files:
        file_path_confirmation_prompt += f"🔸 **{file_name}** has multiple matches:\n"
        for path in paths:
            file_path_confirmation_prompt += f"   - {path}\n"
    file_path_confirmation_prompt += "\n👉 Please specify the correct paths for each above file and also let me know if you have any additional queries."
    return file_path_confirmation_prompt
