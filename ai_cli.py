#!/usr/bin/env python3

import sys
import os
import platform
import subprocess
import argparse
import ollama
from groq import Groq


def get_environment_info():
    return {
        "current_directory": os.getcwd(),
        "os_info": f"{platform.system()} {platform.release()}",
        "shell": os.getenv("SHELL", "unknown shell"),
    }


def query_ollama(prompt: str, model: str = None) -> str:
    try:
        model = model or os.getenv("FAST_OLLAMA_MODEL", "llama3.1")
        response = ollama.generate(
            model=model,
            prompt=prompt,
            options={"num_predict": 128},
            keep_alive="2m",
        )
        return response["response"]
    except Exception as e:
        raise Exception(f"Error querying Ollama: {e}")


def query_groq(prompt: str, model: str = None) -> str:
    try:
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        model = model or "llama-3.1-8b-instant"
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            model=model,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        raise Exception(f"Error querying Groq: {e}")


def query_ai_service(input_text, service_type, model, env_info):
    prompt = f"""You are an expert programmer who is a master of the terminal. 
    Your task is to come up with the perfect command to accomplish the following task. 
    Respond with the command only. No comments. No backticks around the command. 
    The command must be able to be run in the terminal verbatim without error.
    Be sure to accomplish the user's task exactly. 
    You must only return one command. I need to execute your response verbatim.
    Current directory: {env_info['current_directory']}
    Operating System: {env_info['os_info']}
    Shell: {env_info['shell']}
    Do not hallucinate.
    Here is the task: {input_text}"""

    try:
        if service_type == "ollama":
            return query_ollama(prompt, model)
        elif service_type == "groq":
            return query_groq(prompt, model)
        else:
            raise ValueError(f"Unknown service type: {service_type}")
    except Exception as e:
        print(f"Error querying AI service: {e}")
        sys.exit(1)


def execute_command(command):
    try:
        result = subprocess.run(
            command, shell=True, check=True, text=True, capture_output=True
        )
        print(f"Command output:\n{result.stdout}")
        if result.stderr:
            print(f"Error output:\n{result.stderr}")
    except subprocess.CalledProcessError as e:
        print(f"Command failed with return code: {e.returncode}")
        if e.stdout:
            print(f"Command output:\n{e.stdout}")
        if e.stderr:
            print(f"Error output:\n{e.stderr}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate and execute terminal commands using AI."
    )
    parser.add_argument("input", nargs="+", help="The task description")
    parser.add_argument(
        "--service",
        choices=["ollama", "groq"],
        default="ollama",
        help="AI service to use",
    )
    parser.add_argument("--model", help="Optional: Specify the model to use")
    args = parser.parse_args()

    input_text = " ".join(args.input)

    # Only use the model if explicitly specified
    model = args.model if args.model else None

    env_info = get_environment_info()
    command = query_ai_service(input_text, args.service, model, env_info)

    print(f"\033[92m{command}\033[0m")

    confirm = input("Press 'Enter' to execute the command or 'n' to cancel: ")
    if confirm.lower() != "n":
        execute_command(command)
    else:
        print("Command execution cancelled.")


if __name__ == "__main__":
    main()
