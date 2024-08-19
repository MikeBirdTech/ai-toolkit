# AI Commit

Use LLMs to generate your git commit messages.

## Installation

1. Navigate to the `ai_commit` directory
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
3. Set up environment variables:
   - Set `GROQ_API_KEY` for Groq service
   - Set `FAST_OLLAMA_MODEL` to your preferred fast Ollama model (default is "llama3.1")

## Usage

```
python aicommit.py [options]
```

### Options

- `--service {ollama,groq}`: Select the AI service to use (default: ollama)
- `--model MODEL`: Specify a custom model to use (optional)
- `--groq`: Use Groq service instead of Ollama
- `--vim`: Use Vim keys for navigation
- `--num`: Use number selection instead of arrow keys
- `--max_chars=X`: Suggests the maximum commit message length (default is 75 characters)

### Examples

```
python aicommit.py "Fixed bug in login functionality"
python aicommit.py "Added new feature for user authentication" --service groq
python aicommit.py "Refactored code for better performance" --model llama3.1
```

## Notes

- The script will display the generated commit message and ask for confirmation before committing.
- Press Enter to commit or 'n' to cancel.
