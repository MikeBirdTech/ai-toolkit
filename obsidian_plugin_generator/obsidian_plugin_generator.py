import os
import time
import argparse
import subprocess
import json
import re
import shutil
from typing import Dict, Any

import ollama
from groq import Groq, APIError
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.style import Style
from rich.text import Text

console = Console()

ASCII_ART = """
   ___  _         _     _ _                     
  / _ \| |__  ___(_) __| (_) __ _ _ __          
 | | | | '_ \/ __| |/ _` | |/ _` | '_ \         
 | |_| | |_) \__ \ | (_| | | (_| | | | |        
  \___/|_.__/|___/_|\__,_|_|\__,_|_| |_|        
  ____  _             _                         
 |  _ \| |_   _  __ _(_)_ __                    
 | |_) | | | | |/ _` | | '_ \                   
 |  __/| | |_| | (_| | | | | |                  
 |_|   |_|\__,_|\__, |_|_| |_|                  
   ____         |___/             _             
  / ___| ___ _ __   ___ _ __ __ _| |_ ___  _ __ 
 | |  _ / _ \ '_ \ / _ \ '__/ _` | __/ _ \| '__|
 | |_| |  __/ | | |  __/ | | (_| | || (_) | |   
  \____|\___|_| |_|\___|_|  \__,_|\__\___/|_|   
"""

DEFAULT_OBSIDIAN_VAULT_PATH = os.path.expanduser("~/Documents/ObsidianVault")
SAMPLE_PLUGIN_REPO = "https://github.com/obsidianmd/obsidian-sample-plugin.git"
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")
GROQ_MODEL = "llama-3.1-70b-versatile"

PURPLE_STYLE = Style(color="purple")
LIGHT_PURPLE_STYLE = Style(color="bright_magenta")
ORANGE_STYLE = Style(color="#F67504")


class AIService:
    def __init__(self, service_type: str):
        self.service_type = service_type

    def query(self, prompt: str, max_retries: int = 3) -> str:
        retries = 0
        while retries < max_retries:
            try:
                if self.service_type == "ollama":
                    return self.query_ollama(prompt)
                elif self.service_type == "groq":
                    return self.query_groq(prompt)
                else:
                    raise ValueError(f"Unsupported AI service: {self.service_type}")
            except APIError as e:
                retries += 1
                if retries == max_retries:
                    console.print(
                        f"[red]Error: Unable to complete the request after {max_retries} attempts.[/red]"
                    )
                    console.print(f"[yellow]Error details: {str(e)}[/yellow]")
                    console.print(
                        "[yellow]The plugin generation process will continue with default values.[/yellow]"
                    )
                    return "SUFFICIENT INFO"  # Return a default response to continue the process
                else:
                    wait_time = 2**retries  # Exponential backoff
                    console.print(
                        f"[yellow]API error occurred. Retrying in {wait_time} seconds...[/yellow]"
                    )
                    time.sleep(wait_time)

    def query_ollama(self, prompt: str) -> str:
        response = ollama.generate(model=OLLAMA_MODEL, prompt=prompt)
        return response["response"]

    def query_groq(self, prompt: str) -> str:
        try:
            client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=GROQ_MODEL,
            )
            return chat_completion.choices[0].message.content
        except APIError as e:
            console.print(f"[red]Groq API Error: {str(e)}[/red]")
            raise


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
    console.print(
        f"\n[yellow]WARNING:[/yellow] The directory '{plugin_dir}' already exists."
    )
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

        console.print(f"\n[dark_magenta]Q: {next_question}[/dark_magenta]")
        answer = input("Your answer: ")
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

    with console.status("[cyan]Cloning sample plugin...", spinner="dots") as status:
        try:
            subprocess.run(
                ["git", "clone", SAMPLE_PLUGIN_REPO, plugin_dir],
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(["rm", "-rf", os.path.join(plugin_dir, ".git")], check=True)
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Error cloning the sample plugin: {e}[/red]")
            console.print(
                "[yellow]Please make sure you have git installed and have internet access.[/yellow]"
            )
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
    4. Include todo comments for any parts that might need further customization or implementation.
    5. Use async/await for asynchronous operations.
    6. Handle potential errors gracefully.
    7. If using external APIs, implement proper error handling and rate limiting.
    8. Implement a SettingTab if the plugin requires user-configurable settings.

    Provide the complete, valid TypeScript code for the main.ts file within a markdown code block. After the code block, include a brief explanation of the code, any assumptions made, and a todo list for the developer.

    Remember, this should aim to save the user 90% of the time it would take to create the plugin from scratch.
    """
    try:
        generated_content = ai_service.query(prompt)
        processed_content = process_generated_content(generated_content)
    except Exception as e:
        console.print(f"[red]Error generating plugin code: {str(e)}[/red]")
        console.print("[yellow]Using default sample plugin code.[/yellow]")
        processed_content = existing_code

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

    success_message = Text(
        f"Plugin '{plugin_info['name']}' created successfully in {plugin_dir}",
        style=ORANGE_STYLE,
    )
    console.print(Panel(success_message, expand=False, border_style=ORANGE_STYLE))

    next_steps = Table(show_header=False, box=None)
    next_steps.add_column(style=LIGHT_PURPLE_STYLE, no_wrap=True)
    next_steps.add_row(
        "1. Run 'npm install' in the plugin directory to install dependencies."
    )
    next_steps.add_row("2. Install required Python libraries:")
    next_steps.add_row("   npm install obsidian")
    next_steps.add_row(
        "3. Review the enhanced main.ts file, including the commented explanation and todo list at the end."
    )
    next_steps.add_row("4. Complete any to-do items and make necessary adjustments.")
    next_steps.add_row(
        "5. Run 'npm run dev' to compile the plugin and start the development process."
    )
    next_steps.add_row(
        "6. Test your plugin in Obsidian and make any further adjustments as needed."
    )
    next_steps.add_row(
        "7. When ready to use, ensure the plugin is compiled with 'npm run build'."
    )

    console.print(
        Panel(
            next_steps,
            expand=False,
            border_style=PURPLE_STYLE,
            title="Next Steps",
            title_align="center",
        )
    )


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

    ascii_text = Text(ASCII_ART)
    ascii_text.stylize("purple", 0, 380)
    ascii_text.stylize("dark_magenta", 380, 600)
    ascii_text.stylize("bright_magenta", 600, 796)
    console.print(ascii_text)

    ai_service = AIService(args.ai_service)

    plugin_info = {
        "name": args.name,
        "id": args.name.lower().replace(" ", "-"),
        "description": input(
            "Enter a general description of what your plugin will do: "
        ),
        "vault_path": args.vault_path,
    }

    create_plugin(ai_service, plugin_info)


if __name__ == "__main__":
    main()
