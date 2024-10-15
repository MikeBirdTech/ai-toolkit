# AI Service

This module provides a unified interface for interacting with various AI services, including Ollama, Groq, and Anthropic.

## Features

- Supports multiple AI services (Ollama, Groq, Anthropic)
- Configurable service type and model
- Automatic retry mechanism for failed queries

## Usage

```python
from ai_service import AIService

# Initialize the AI service
ai_service = AIService(service_type="ollama", model="llama3.1")

# Query the AI service
response = ai_service.query("What is the capital of France?")
print(response)
```

## Configuration

The `AIService` class requires the following environment variables to be set:

- `OLLAMA_BASE_URL`: Base URL for Ollama API (required if using Ollama)
- `GROQ_API_KEY`: API key for Groq (required if using Groq)
- `ANTHROPIC_API_KEY`: API key for Anthropic (required if using Anthropic)

## Installation

1. Ensure you have Python 3.6 or higher installed.
2. Install the required dependencies:

```
pip install -r requirements.txt
```

## License

[Specify the license here]
