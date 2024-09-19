import os
import sys
import re
import json
import logging
from github import Github
from groq import Groq

# Setup logging
logging.basicConfig(level=logging.INFO)

# Initialize clients
try:
    groq_client = Groq(api_key=os.environ["GROQ_API_KEY"])
    g = Github(os.environ["GITHUB_TOKEN"])
except KeyError as e:
    logging.error(f"Environment variable not set: {e}")
    sys.exit(1)


def scan_for_todos():
    todos = []
    exclude_dirs = {".git", "venv", "__pycache__", "node_modules", ".github"}
    exclude_exts = {
        ".pyc",
        ".md",
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

    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith(".")]
        for file in files:
            if any(file.endswith(ext) for ext in exclude_exts):
                continue
            file_path = os.path.join(root, file)
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    for i, line in enumerate(f):
                        if "TODO" in line:
                            todos.append(
                                {
                                    "file": file_path,
                                    "line_number": i + 1,
                                    "line": line.strip(),
                                }
                            )
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

Provide the output in valid JSON format as an array of objects, each with "title" and "body" fields.

Here are the TODO items:

"""

    for todo in todo_items:
        prompt += f"File: {todo['file']}, Line: {todo['line_number']}, Comment: {todo['line']}\n"

    response = groq_client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.1-70b-versatile",
        temperature=0.5,
        max_tokens=1000,
    )

    content = response.choices[0].message.content

    # Ensure the response is valid JSON
    try:
        issues = json.loads(content)
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse LLM response as JSON: {e}")
        issues = []
    return issues


def create_issues(repo_name, issues):
    repo = g.get_repo(repo_name)
    existing_issues = repo.get_issues(state="open")
    existing_titles = {issue.title for issue in existing_issues}

    for issue in issues:
        title = issue.get("title")
        body = issue.get("body")

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
