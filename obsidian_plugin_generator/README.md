# Obsidian Plugin Generator

An intelligent tool to generate custom Obsidian plugins based on user descriptions and answers.

## Demo Video

[![Obsidian Plugin Generator Demo](https://img.youtube.com/vi/YXgOXf6oDBQ/0.jpg)](https://www.youtube.com/watch?v=YXgOXf6oDBQ)

Click the image above to watch the demo of using the Obsidian Plugin Generator.

## Installation

1. Navigate to the `obsidian_plugin_generator` directory
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
3. Set up environment variables:
   - `GROQ_API_KEY`: Your Groq API key (if using Groq)
   - `OLLAMA_MODEL`: Your preferred Ollama model (default is "llama3.1")

## Usage

```
python obsidian_plugin_generator.py [plugin_name] [options]
```

### Options

- `--vault-path PATH`: Path to Obsidian vault (default: ~/Documents/ObsidianVault)
- `--ai-service {ollama,groq}`: AI service to use (default: ollama)

### Examples

```
python obsidian_plugin_generator.py "My Custom Plugin"
python obsidian_plugin_generator.py "Task Tracker" --vault-path ~/Obsidian/MyVault
python obsidian_plugin_generator.py "Code Snippets" --ai-service groq
```

## Features

- AI-powered plugin generation based on user descriptions
- Supports multiple AI services: Ollama and Groq
- Automatically clones and modifies the Obsidian sample plugin
- Generates enhanced TypeScript code for the plugin
- Handles existing directories with options to overwrite, rename, or cancel
- Provides next steps for plugin development and testing

## Output

The script generates a new Obsidian plugin directory in your vault's `.obsidian/plugins` folder, containing:

1. `main.ts`: The main TypeScript file with AI-generated plugin code
2. `manifest.json`: Plugin manifest file with updated metadata
3. `package.json`: Package configuration file with updated metadata
4. Other necessary files from the sample plugin

## Notes

- Ensure you have Git installed and accessible from the command line
- The script requires an active internet connection to clone the sample plugin
- Review and complete any TODOs left in the generated code
- Follow the "Next Steps" provided after plugin generation for further development

## Requirements

- Python 3.6+
- Git
- Node.js and npm (for plugin development)
