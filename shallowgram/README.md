# Shallowgram

A local speech analysis tool that transcribes audio, summarizes content, and provides insights using AI.

## Installation

1. Navigate to the `shallowgram` directory
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
3. Set up environment variables:

   - `OLLAMA_MODEL`: Your preferred Ollama model (default is "llama3.1")

4. Install FFmpeg on your system (required for audio conversion)

## Usage

```
python shallowgram.py [options]
```

### Options

- `--model MODEL`: Whisper model to use (default: tiny.en)
- `--whisperfile_path PATH`: Path to the whisperfile directory
- `--vault_path PATH`: Path to the Obsidian vault directory
- `--summarize`: Summarize the transcribed text
- `--sentiment`: Analyze sentiment of the transcribed text
- `--intent`: Detect intent in the transcribed text
- `--topics`: Detect topics in the transcribed text
- `--markdown`: Export results to markdown in Obsidian vault
- `--input_file FILE`: Input audio file (wav, mp3, ogg, or flac)
- `--verbose`: Enable verbose output
- `--full`: Enable full rich output with all features

### Examples

```
python shallowgram.py --full
python shallowgram.py --input_file audio.mp3 --summarize --sentiment
python shallowgram.py --model medium.en --markdown --vault_path /path/to/vault
```

## Features

- Audio recording and transcription using Whisper models
- Support for various audio input formats (wav, mp3, ogg, flac)
- AI-powered summarization, sentiment analysis, intent detection, and topic extraction
- Rich console output with colorized results
- Export results to markdown files in Obsidian vault
- Customizable Whisper model selection

## Output

The script generates:

1. Transcription of the audio input
2. Summary of the transcribed text (if requested)
3. Sentiment analysis (if requested)
4. Intent detection (if requested)
5. Topic extraction (if requested)
6. Markdown file with all results (if requested)

## Notes

- Ensure FFmpeg is installed on your system for audio conversion
- The script uses Ollama for AI processing, ensure it's properly set up
- Whisper models are downloaded automatically if not found in the specified path
- Temporary audio files are automatically cleaned up after processing

## Requirements

- Python 3.6+
- FFmpeg
- Ollama
- Internet connection (to download whisperfiles)
