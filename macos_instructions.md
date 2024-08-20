# macOS Instructions

General instructions for setting up and running the scripts on macOS

## Pre-requisites

Install the following:

- `brew install python3 fzf`

## Setup

1. Clone the repository:

   ```
   git clone https://github.com/MikeBirdTech/automations.git && cd automations
   ```

2. Create and activate a virtual environment:

   ```
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install the required packages:

   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables:

   ```
   export EXA_API_KEY="<your exa api key>"
   export GROQ_API_KEY="<your groq api key>"
   export ANTHROPIC_API_KEY="<your anthropic api key>"
   export FAST_OLLAMA_MODEL="<your preferred fast Ollama model>"
   export OLLAMA_MODEL="<your preferred Ollama model, default is llama3.1>"
   ```

   Note: You may want to add these environment variables to your shell configuration file (e.g., `.bashrc` or `.zshrc`) for persistence across sessions.

## Running Scripts

Navigate to the specific script directory and refer to its README for detailed usage instructions.

For example:

- AI Commit: `cd ai_commit && python aicommit.py`
- AI CLI: `cd ai_cli && python ai_cli.py`
- Research Assistant: `cd research_assistant && python research_assistant.py`

Refer to each script's README for specific options and usage details.
