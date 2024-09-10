# Activity Tracker

An AI-powered tool to track activities, categorize them, and provide insights on time usage and productivity.

## Installation

1. Navigate to the `activity_tracker` directory
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
3. Set up environment variables:
   - `GROQ_API_KEY`: Your Groq API key (if using Groq)
   - `OLLAMA_MODEL`: Your preferred Ollama model (default is "llama3.1")

## Usage

```
python activity_tracker.py [options]
```

### Options

- `--ai-service {groq,ollama}`: AI service to use for categorization and insights (default: groq)
- `--voice`: Use voice input for activities instead of text input
- `--vault-path PATH`: Path to Obsidian vault (default: /Users/mike/Documents/obs-test/TEST)

### Examples

```
python activity_tracker.py
python activity_tracker.py --ai-service ollama --voice
python activity_tracker.py --vault-path /path/to/your/obsidian/vault
python activity_tracker.py --ai-service groq --voice --vault-path /path/to/your/obsidian/vault
```

## Features

- AI-powered activity categorization and insights
- Voice input support for activity descriptions
- Integration with Obsidian for daily activity tracking
- Multiple AI service support: Ollama and Groq
- Real-time activity tracking with start/stop functionality
- Activity statistics and productivity insights

## Output

The script generates and updates a daily markdown file in your Obsidian vault:

1. Activities section: List of tracked activities with timestamps, categories, and durations
2. Summary section: Total activities and total time tracked
3. Insights section: AI-generated insights about time usage and productivity

## Notes

- Ensure you have the necessary API keys set up as environment variables
- The script uses a default Obsidian vault path, which can be customized using the `--vault-path` option
- Voice input requires additional audio dependencies (PyAudio and SpeechRecognition)

## Requirements

- Python 3.6+
- PyAudio (for voice input functionality)
- Internet connection (for AI services)
