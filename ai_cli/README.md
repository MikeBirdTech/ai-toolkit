# AI CLI

Use LLMs to generate terminal commands from natural language queries.

## Installation

1. Navigate to the `ai_cli` directory
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
3. Make the script executable:
   ```
   chmod +x ai_cli.py
   ```
4. Set up environment variables:
   - Set `GROQ_API_KEY` for Groq service
   - Set `FAST_OLLAMA_MODEL` to your preferred fast Ollama model (optional)

## Usage

```
python ai_cli.py [input] [options]
```

### Options

- `--service {ollama,groq}`: Select the AI service to use (default: ollama)
- `--model MODEL`: Specify a custom model to use (optional)

### Examples

```
python ai_cli.py "List all files in the current directory"
python ai_cli.py "Create a new directory named 'test'" --service groq
python ai_cli.py "Show system information" --model codestral
```

## Notes

- The script will display the generated command and ask for confirmation before execution.
- Press Enter to execute the command or 'n' to cancel.
