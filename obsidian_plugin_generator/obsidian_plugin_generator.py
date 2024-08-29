import os
import sys
import argparse
import subprocess
import json
import re
import shutil
from typing import Dict, Any

import ollama
from groq import Groq

DEFAULT_OBSIDIAN_VAULT_PATH = os.path.expanduser("~/Documents/ObsidianVault")
SAMPLE_PLUGIN_REPO = "https://github.com/obsidianmd/obsidian-sample-plugin.git"
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")
GROQ_MODEL = "llama-3.1-70b-versatile"


class AIService:
    def __init__(self, service_type: str):
        self.service_type = service_type

    def query(self, prompt: str) -> str:
        if self.service_type == "ollama":
            return self.query_ollama(prompt)
        elif self.service_type == "groq":
            return self.query_groq(prompt)
        else:
            raise ValueError(f"Unsupported AI service: {self.service_type}")

    def query_ollama(self, prompt: str) -> str:
        response = ollama.generate(model=OLLAMA_MODEL, prompt=prompt)
        return response["response"]

    def query_groq(self, prompt: str) -> str:
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=GROQ_MODEL,
        )
        return chat_completion.choices[0].message.content


def read_file(file_path: str) -> str:
    with open(file_path, "r") as f:
        return f.read()


def write_file(file_path: str, content: str) -> None:
    with open(file_path, "w") as f:
        f.write(content)


def get_next_question(
    ai_service: AIService,
    plugin_info: Dict[str, Any],
    conversation_history: str,
    is_final: bool,
) -> str:
    if is_final:
        prompt = f"""
        Based on the following Obsidian plugin idea and conversation history, determine if you have enough information to create a comprehensive plugin. If you do, respond with "SUFFICIENT INFO". If not, ask one final question to gather the most critical information needed.

        Plugin Name: {plugin_info['name']}
        Plugin Description: {plugin_info['description']}

        Conversation History:
        {conversation_history}

        Provide only the question or "SUFFICIENT INFO", without any additional text.
        """
    else:
        prompt = f"""
        Based on the following Obsidian plugin idea and conversation history, determine if more information is needed to create a comprehensive plugin. If more information is needed, ask ONE specific, open-ended question to gather that information. If sufficient information has been gathered, respond with "SUFFICIENT INFO".

        Plugin Name: {plugin_info['name']}
        Plugin Description: {plugin_info['description']}

        Conversation History:
        {conversation_history}

        Provide only the question or "SUFFICIENT INFO", without any additional text.
        """

    return ai_service.query(prompt).strip()


def process_generated_content(content: str) -> str:
    # Split the content into code and explanation
    parts = content.split("```", 2)

    if len(parts) >= 3:
        code = parts[1].strip()
        explanation = parts[2].strip()

        # Remove 'typescript' from the beginning of the code if present
        code = re.sub(r"^typescript\n", "", code)

        # Convert the explanation into a multi-line comment
        commented_explanation = "/*\n" + explanation + "\n*/"

        return f"{code}\n\n{commented_explanation}"
    else:
        return content.strip()


def handle_existing_directory(plugin_dir: str) -> bool:
    print(f"\nWARNING: The directory '{plugin_dir}' already exists.")
    while True:
        choice = input("Do you want to (O)verwrite, (R)ename, or (C)ancel? ").lower()
        if choice == "o":
            shutil.rmtree(plugin_dir)
            return True
        elif choice == "r":
            new_name = input("Enter a new name for the plugin: ")
            new_dir = os.path.join(
                os.path.dirname(plugin_dir), new_name.lower().replace(" ", "-")
            )
            if os.path.exists(new_dir):
                print(
                    f"The directory '{new_dir}' also exists. Please choose a different name."
                )
            else:
                return new_dir
        elif choice == "c":
            return False
        else:
            print("Invalid choice. Please enter 'O', 'R', or 'C'.")


def create_plugin(ai_service: AIService, plugin_info: Dict[str, Any]) -> None:
    conversation_history = ""
    for i in range(3):
        is_final = i == 2
        next_question = get_next_question(
            ai_service, plugin_info, conversation_history, is_final
        )

        if next_question == "SUFFICIENT INFO":
            break

        print(f"\nQ: {next_question}")
        print("-" * 40)
        answer = input("Your answer: ")
        print("-" * 40)
        conversation_history += f"Q: {next_question}\nA: {answer}\n\n"

    plugin_dir = os.path.join(
        plugin_info["vault_path"], ".obsidian", "plugins", plugin_info["id"]
    )

    if os.path.exists(plugin_dir):
        result = handle_existing_directory(plugin_dir)
        if isinstance(result, str):
            plugin_dir = result
            plugin_info["id"] = os.path.basename(plugin_dir)
        elif not result:
            print("Plugin creation cancelled.")
            return

    os.makedirs(plugin_dir, exist_ok=True)

    try:
        # Clone sample plugin and remove .git directory
        subprocess.run(["git", "clone", SAMPLE_PLUGIN_REPO, plugin_dir], check=True)
        subprocess.run(["rm", "-rf", os.path.join(plugin_dir, ".git")], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error cloning the sample plugin: {e}")
        print("Please make sure you have git installed and have internet access.")
        return

    # Read existing main.ts
    main_ts_path = os.path.join(plugin_dir, "main.ts")
    existing_code = read_file(main_ts_path)

    # Generate enhanced code
    prompt = f"""
    Enhance the following Obsidian plugin code for a plugin named "{plugin_info['name']}" with the description: "{plugin_info['description']}".

    Additional information from the conversation:
    {conversation_history}

    Existing code:
    {existing_code}

    Please modify the existing code to implement the functionality described. Consider all the information provided and be creative in implementing features that align with the plugin's purpose. The plugin should be able to do any or all of the following:
    - Interact with the editor
    - Add commands to the command palette
    - Modify the UI
    - Store settings or data if necessary

    Requirements:
    1. Use TypeScript and follow Obsidian plugin best practices.
    2. Ensure the plugin follows the correct anatomy with onload() and onunload() methods.
    3. Add clear comments explaining the code and any assumptions made.
    4. Include TODO comments for any parts that might need further customization or implementation.
    5. Use async/await for asynchronous operations.
    6. Handle potential errors gracefully.
    7. If using external APIs, implement proper error handling and rate limiting.
    8. Implement a SettingTab if the plugin requires user-configurable settings.

    Provide the complete, valid TypeScript code for the main.ts file within a markdown code block. After the code block, include a brief explanation of the code, any assumptions made, and a todo list for the developer.

    Remember, this should aim to save the user 90% of the time it would take to create the plugin from scratch.
    """
    generated_content = ai_service.query(prompt)
    processed_content = process_generated_content(generated_content)

    # Write the processed content to main.ts
    write_file(main_ts_path, processed_content)

    # Update manifest.json and package.json
    for file in ["manifest.json", "package.json"]:
        file_path = os.path.join(plugin_dir, file)
        with open(file_path, "r+") as f:
            data = json.load(f)
            data["name"] = plugin_info["name"]
            data["id"] = plugin_info["id"]
            data["description"] = plugin_info["description"]
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()

    print(f"\nPlugin '{plugin_info['name']}' created successfully in {plugin_dir}")
    print("\nNext steps:")
    print("=" * 40)
    print(
        "1. Review the enhanced main.ts file, including the commented explanation and todo list at the end."
    )
    print("2. Complete any TODOs and make necessary adjustments.")
    print("3. Run 'npm install' in the plugin directory to install dependencies.")
    print(
        "4. Run 'npm run dev' to compile the plugin and start the development process."
    )
    print("5. Test your plugin in Obsidian and make any further adjustments as needed.")
    print("6. When ready to use, ensure the plugin is compiled with 'npm run build'.")
    print("=" * 40)


def main():
    parser = argparse.ArgumentParser(description="Obsidian Plugin Generator")
    parser.add_argument("name", help="Name of the plugin")
    parser.add_argument(
        "--vault-path",
        default=DEFAULT_OBSIDIAN_VAULT_PATH,
        help="Path to Obsidian vault",
    )
    parser.add_argument(
        "--ai-service",
        choices=["ollama", "groq"],
        default="ollama",
        help="AI service to use",
    )
    args = parser.parse_args()

    ai_service = AIService(args.ai_service)

    plugin_info = {
        "name": args.name,
        "id": args.name.lower().replace(" ", "-"),
        "description": input(
            "Enter a general description of what the plugin should do: "
        ),
        "vault_path": args.vault_path,
    }

    create_plugin(ai_service, plugin_info)


if __name__ == "__main__":
    main()
