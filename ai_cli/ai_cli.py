#!/usr/bin/env python
import argparse
import os
import platform
import subprocess
import sys

from ai_service.ai_service import AIService


def get_environment_info():
    return {
        "current_directory": os.getcwd(),
        "os_info": f"{platform.system()} {platform.release()}",
        "shell": os.getenv("SHELL", "unknown shell"),
    }



def query_ai_service(input_text, service_type, model, env_info):
    ai_service = AIService(service_type, model)
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
        return ai_service.query(prompt)
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
    parser = argparse.ArgumentParser(description="AI CLI Tool")
    parser.add_argument("input", nargs="*", help="Input text for the AI")
    parser.add_argument("--service", choices=["ollama", "groq", "anthropic"], default="ollama", help="AI service to use")
    parser.add_argument("--model", help="Model to use for the selected service")
    args = parser.parse_args()

    input_text = " ".join(args.input)
    env_info = get_environment_info()

    command = query_ai_service(input_text, args.service, args.model, env_info)

    print(f"\033[92m{command}\033[0m")

    confirm = input("Press 'Enter' to execute the command or 'n' to cancel: ")
    if confirm.lower() != "n":
        execute_command(command)
    else:
        print("Command execution cancelled.")


if __name__ == "__main__":
    main()
