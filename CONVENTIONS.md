# Conventions for LLMs

1. Project Structure:

   - Maintain separate directories for each tool.

2. AI Models:

   - Default to groq for LLM inference, if not specified.
   - AI Models:
     - Ollama: Use "llama3.1" as the default model.
     - Groq: Use "llama-3.1-70b-versatile" as the default model.
     - Anthropic: Use "claude-3-5-sonnet-20240620" as the default model.

3. AI Service Integration:

   - Use the AIService class from ai_service/ai_service.py for all interactions with AI services.
   - Support multiple AI services (Ollama, Groq, Anthropic) in tools where applicable.

4. Command-Line Interfaces:

   - Use argparse for parsing command-line arguments.
   - Include options for selecting AI service, model, and other tool-specific settings.

5. README Files:

   - Include a README.md in each tool's directory with installation, usage, and example commands.
   - Use code blocks for installation steps and usage examples.

6. Requirements:

   - Maintain a requirements.txt file for each tool with its specific dependencies.

7. Output Formatting:

   - Use the 'rich' library for enhanced console output where appropriate.
   - Whenever possible, format output as markdown for tools that generate documentation or reports.

8. AI Prompt Engineering:

   - Structure AI prompts clearly, often using multi-line strings for readability.
   - Include specific instructions in prompts (e.g., character limits, formatting requirements).

9. Obsidian Integration:

   - For tools that interact with Obsidian, use consistent methods for vault path handling and file creation.

10. Audio Processing:

    - Handle various audio formats and provide conversion options.

11. Performance Considerations:

    - Implement timeouts and retries for API calls.
    - Consider asynchronous operations for I/O-bound tasks.

12. Security:

    - Never hardcode API keys or tokens. Always use environment variables.
