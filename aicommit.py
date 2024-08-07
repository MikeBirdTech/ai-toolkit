#!/usr/bin/env python
import sys
import os
import ollama
import subprocess
import argparse
import time
from typing import List, Optional
from groq import Groq

# Use the environment variable for the Ollama model
OLLAMA_MODEL = os.getenv("FAST_OLLAMA_MODEL", "llama3.1")
GROQ_MODEL = "llama-3.1-8b-instant"


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


def query_ollama(prompt: str) -> str:
    """Query Ollama with the given prompt."""
    try:
        print("Generating commit messages...", end="", flush=True)
        response = ollama.generate(
            model=OLLAMA_MODEL,
            prompt=prompt,
            system="You are an expert programmer that values clear, unambiguous communication and are specialized in generating concise and informative git commit messages.",
            options={
                "num_predict": 128,
            },
            keep_alive="2m",
        )
        print("Done!")
        return response["response"]
    except Exception as e:
        print(f"\nError querying Ollama: {e}")
        sys.exit(1)


def query_groq(prompt: str) -> str:
    """Query Groq with the given prompt."""
    try:
        print("Generating commit messages...", end="", flush=True)
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert programmer that values clear, unambiguous communication and are specialized in generating concise and informative git commit messages.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            model=GROQ_MODEL,
        )
        print("Done!")
        return chat_completion.choices[0].message.content
    except Exception as e:
        print(f"\nError querying Groq: {e}")
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
    parser = argparse.ArgumentParser(
        description="Generate git commit messages using LLMs."
    )
    parser.add_argument(
        "--groq", action="store_true", help="Use Groq API instead of Ollama"
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
        "--max_chars", type=int, default=75, help="Maximum number of characters for each commit message (default: 75)"
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
        response = query_groq(prompt)
    else:
        response = query_ollama(prompt)

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
                response = query_groq(prompt)
            else:
                response = query_ollama(prompt)
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
