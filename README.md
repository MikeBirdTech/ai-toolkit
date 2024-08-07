# Automations

A collection of community created scripts to automate your life

## AI CLI

Use LLMs to generate terminal commands from natural language queries.

### Installation

- `pip install groq`
- `pip install ollama`
- set `GROQ_API_KEY`
- set `FAST_OLLAMA_MODEL` to your fast Ollama model of choice

Options

- Can use `--service` to select between `groq` and `ollama`
- Can use `--model` to select a model

## AI Commit

Use LLMs to generate your commit messages.

### Installation

Requires

- `pip install groq`
- `pip install ollama`
- set `GROQ_API_KEY`
- set `FAST_OLLAMA_MODEL` to your fast Ollama model of choice

Options

- Local by default
- Use Groq with `--groq`
- Arrow keys by default
- Use Vim keys with `--vim`
- Use number selection with `--num`
