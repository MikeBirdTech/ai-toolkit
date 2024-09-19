import os
import sys
import re
import json
import logging
from github import Github
from groq import Groq
import instructor
from pydantic import BaseModel, RootModel
from typing import List

# Setup logging
logging.basicConfig(level=logging.INFO)

# Initialize clients
try:
    groq_client = Groq(api_key=os.environ["GROQ_API_KEY"])
    # Patch the client with instructor
    groq_client = instructor.from_groq(groq_client, mode=instructor.Mode.TOOLS)
    g = Github(os.environ["GITHUB_TOKEN"])
except KeyError as e:
    logging.error(f"Environment variable not set: {e}")
    sys.exit(1)


class Issue(BaseModel):
    title: str
    body: str


class IssuesResponse(BaseModel):
    issues: List[Issue]


def scan_for_todos():
    todos = []
    exclude_dirs = {".git", "venv", "__pycache__", "node_modules", ".github"}
    exclude_exts = {
        ".pyc",
        ".json",
        ".yaml",
        ".yml",
        ".lock",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".svg",
    }

    # Define comment styles for different file extensions
    comment_styles = {
        ".py": {"single": ["#"], "multi": [('"""', '"""'), ("'''", "'''")]},
        ".js": {"single": ["//"], "multi": [("/*", "*/")]},
        ".ts": {"single": ["//"], "multi": [("/*", "*/")]},
        ".java": {"single": ["//"], "multi": [("/*", "*/")]},
        ".c": {"single": ["//"], "multi": [("/*", "*/")]},
        ".cpp": {"single": ["//"], "multi": [("/*", "*/")]},
        ".md": {"single": ["<!--"], "multi": [("<!--", "-->")]},
        ".sh": {"single": ["#"], "multi": []},
        # Add more file extensions and their comment styles as needed
    }

    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith(".")]
        for file in files:
            if any(file.endswith(ext) for ext in exclude_exts):
                continue

            file_path = os.path.join(root, file)
            file_ext = os.path.splitext(file)[1]
            comment_style = comment_styles.get(file_ext)

            if not comment_style:
                # Skip files with unknown extensions
                continue

            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                    # Initialize a set to keep track of line numbers where TODOs are found
                    todo_line_numbers = set()

                    # Handle multi-line comments
                    for start_delim, end_delim in comment_style.get("multi", []):
                        pattern = (
                            re.escape(start_delim) + r"(.*?)" + re.escape(end_delim)
                        )
                        matches = re.finditer(pattern, content, re.DOTALL)

                        for match in matches:
                            comment_content = match.group(1)
                            if "TODO" in comment_content:
                                # Find line numbers for multi-line comments
                                start_pos = match.start()
                                line_number = content[:start_pos].count("\n") + 1
                                todos.append(
                                    {
                                        "file": file_path,
                                        "line_number": line_number,
                                        "line": comment_content.strip(),
                                    }
                                )
                                todo_line_numbers.add(line_number)

                    # Handle single-line comments
                    lines = content.splitlines()
                    for i, line in enumerate(lines):
                        stripped_line = line.strip()
                        for single_comment in comment_style.get("single", []):
                            if stripped_line.startswith(single_comment):
                                comment_text = stripped_line[
                                    len(single_comment) :
                                ].strip()
                                if (
                                    "TODO" in comment_text
                                    and (i + 1) not in todo_line_numbers
                                ):
                                    todos.append(
                                        {
                                            "file": file_path,
                                            "line_number": i + 1,
                                            "line": comment_text,
                                        }
                                    )
                                break  # No need to check other single-line comment styles
            except Exception as e:
                logging.warning(f"Could not read file {file_path}: {e}")

    return todos


def generate_issue_body(todo_items):
    prompt = """
You are an AI assistant that helps developers by turning TODO comments into GitHub issues.

Each TODO comment includes a file path, line number, and the comment text.

Please generate a detailed issue description for each TODO, including:

- A clear and concise title.
- The context or purpose of the TODO.
- Any suggested implementation details.
- Any potential impact or dependencies.

Provide the output as a JSON object with an "issues" field containing an array of objects, each with "title" and "body" fields.

Here are the TODO items:

"""

    for todo in todo_items:
        prompt += f"File: {todo['file']}, Line: {todo['line_number']}, Comment: {todo['line']}\n"

    messages = [{"role": "user", "content": prompt}]

    try:
        response: IssuesResponse = groq_client.chat.completions.create(
            messages=messages,
            model="llama-3.1-70b-versatile",
            temperature=0.1,
            max_tokens=1000,
            response_model=IssuesResponse,
        )
        issues = response.issues
    except Exception as e:
        logging.error(f"Failed to parse LLM response: {e}")
        issues = []

    return issues


def create_issues(repo_name, issues):
    repo = g.get_repo(repo_name)
    existing_issues = repo.get_issues(state="open")
    existing_titles = {issue.title for issue in existing_issues}

    for issue in issues:
        title = issue.title
        body = issue.body

        if not title or not body:
            logging.warning("Issue title or body is missing. Skipping issue.")
            continue

        if title in existing_titles:
            logging.info(f"Issue '{title}' already exists. Skipping.")
            continue

        try:
            repo.create_issue(title=title, body=body)
            logging.info(f"Issue created: {title}")
        except Exception as e:
            logging.error(f"Failed to create issue '{title}': {e}")


def main():
    logging.info("Scanning codebase for TODO comments...")
    todo_items = scan_for_todos()
    if not todo_items:
        logging.info("No TODO comments found.")
        return

    logging.info(f"Found {len(todo_items)} TODO comments.")
    issues = generate_issue_body(todo_items)
    if not issues:
        logging.info("No issues generated.")
        return

    repo_name = os.environ.get("GITHUB_REPOSITORY")
    if not repo_name:
        logging.error("GITHUB_REPOSITORY environment variable not set.")
        sys.exit(1)

    logging.info("Creating issues in GitHub repository...")
    create_issues(repo_name, issues)


if __name__ == "__main__":
    main()
