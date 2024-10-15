#!/usr/bin/env python
import argparse
import os
import subprocess
import sys
import time
from typing import List, Optional

from ai_service.ai_service import AIService


def get_git_diff() -> str:
    """Get the git diff of staged changes, or unstaged if no staged changes."""
    try:
        diff = subprocess.check_output(["git", "diff", "--cached"], text=True)
        if not diff:
            diff = subprocess.check_output(["git", "diff"], text=True)
        return diff[:5000]  # Limit to 5000 characters
    except subprocess.CalledProcessError:
        print("Error: Not a git repository or git is not installed.")
        sys.exit(1)


def query_ai_service(
    prompt: str, service_type: str, ollama_model: str, groq_model: str
) -> str:
    """Query AI service with the given prompt."""
    try:
        print("Generating commit messages...", end="", flush=True)
        ai_service = AIService(
            service_type, model=ollama_model if service_type == "ollama" else groq_model
        )
        response = ai_service.query(prompt)
        print("Done!")
        return response
    except Exception as e:
        print(f"\nError querying {service_type.capitalize()}: {e}")
        sys.exit(1)


def parse_commit_messages(response: str) -> List[str]:
    """Parse the LLM response into a list of commit messages."""
    messages = []
    for line in response.split("\n"):
        if line.strip().startswith(("1.", "2.", "3.")):
            messages.append(line.split(".", 1)[1].strip())
    return messages


def select_message_with_fzf(
    messages: List[str], use_vim: bool = False, use_num: bool = False
) -> Optional[str]:
    """Use fzf to select a commit message, with option to regenerate."""
    try:
        messages.append("Regenerate messages")
        fzf_args = [
            "fzf",
            "--height=10",
            "--layout=reverse",
            "--prompt=Select a commit message (ESC to cancel): ",
            "--no-info",
            "--margin=1,2",
            "--border",
            "--color=prompt:#D73BC9,pointer:#D73BC9",
        ]

        if use_vim:
            fzf_args.extend(["--bind", "j:down,k:up"])

        if use_num:
            for i, msg in enumerate(messages):
                messages[i] = f"{i+1}. {msg}"
            fzf_args.extend(
                [
                    "--bind",
                    "1:accept-non-empty,2:accept-non-empty,3:accept-non-empty,4:accept-non-empty",
                ]
            )

        result = subprocess.run(
            fzf_args,
            input="\n".join(messages),
            capture_output=True,
            text=True,
        )
        if result.returncode == 130:  # User pressed ESC
            return None
        selected = result.stdout.strip()
        if selected == "Regenerate messages" or selected == "4. Regenerate messages":
            return "regenerate"
        return selected.split(". ", 1)[1] if use_num and selected else selected
    except subprocess.CalledProcessError:
        print("Error: fzf selection failed.")
        return None


def create_commit(message: str):
    """Create a git commit with the selected message."""
    try:
        subprocess.run(["git", "commit", "-m", message], check=True)
        print(f"Committed with message: {message}")
    except subprocess.CalledProcessError:
        print("Error: Failed to create commit.")
        sys.exit(1)


def main():
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")
    GROQ_MODEL = "llama-3.1-70b-versatile"

    parser = argparse.ArgumentParser(
        description="Generate git commit messages using LLMs."
    )
    parser.add_argument(
        "--groq",
        action="store_true",
        help="Use Groq API instead of Ollama (default is Ollama)",
    )
    parser.add_argument(
        "--analytics", action="store_true", help="Display performance analytics"
    )
    parser.add_argument(
        "--vim", action="store_true", help="Use vim-style navigation in fzf"
    )
    parser.add_argument(
        "--num", action="store_true", help="Use number selection for commit messages"
    )
    parser.add_argument(
        "--max_chars",
        type=int,
        default=75,
        help="Suggested maximum number of characters for each commit message (default: 75)",
    )
    args = parser.parse_args()

    start_time = time.time()

    diff = get_git_diff()
    if not diff:
        print("No changes to commit.")
        sys.exit(0)

    prompt = f"""
    Your task is to generate three concise, informative git commit messages based on the following git diff.
    Be sure that each commit message reflects the entire diff.
    It is very important that the entire commit is clear and understandable with each of the three options. 
    Try to fit each commit message in {args.max_chars} characters.
    Each message should be on a new line, starting with a number and a period (e.g., '1.', '2.', '3.').
    Here's the diff:\n\n{diff}"""

    if args.groq:
        response = query_ai_service(prompt, "groq", OLLAMA_MODEL, GROQ_MODEL)
    else:
        response = query_ai_service(prompt, "ollama", OLLAMA_MODEL, GROQ_MODEL)

    end_time = time.time()

    if args.analytics:
        print(f"\nAnalytics:")
        print(
            f"Time taken to generate commit messages: {end_time - start_time:.2f} seconds"
        )
        print(f"Inference used: {'Groq' if args.groq else 'Ollama'}")
        print(f"Model name: {GROQ_MODEL if args.groq else OLLAMA_MODEL}")
        print("")  # Add a blank line for better readability

    commit_messages = parse_commit_messages(response)
    if not commit_messages:
        print("Error: Could not generate commit messages.")
        sys.exit(1)

    while True:
        selected_message = select_message_with_fzf(
            commit_messages, use_vim=args.vim, use_num=args.num
        )
        if selected_message == "regenerate":
            start_time = time.time()
            if args.groq:
                response = query_ai_service(prompt, "groq", OLLAMA_MODEL, GROQ_MODEL)
            else:
                response = query_ai_service(prompt, "ollama", OLLAMA_MODEL, GROQ_MODEL)
            end_time = time.time()

            if args.analytics:
                print(f"\nRegeneration Analytics:")
                print(
                    f"Time taken to regenerate commit messages: {end_time - start_time:.2f} seconds"
                )
                print("")  # Add a blank line for better readability

            commit_messages = parse_commit_messages(response)
            if not commit_messages:
                print("Error: Could not generate commit messages.")
                sys.exit(1)
        elif selected_message:
            create_commit(selected_message)
            break
        else:
            print("Commit messages rejected. Please create commit message manually.")
            break


if __name__ == "__main__":
    main()
