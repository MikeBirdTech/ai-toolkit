# macOS Instructions

How to run the scripts on macOS

## Pre-requisites

Install the following:
- `brew install python3 fzf`

## AI Commit

In macOS shell run:

- `git clone https://github.com/MikeBirdTech/automations.git && cd automations`
- `python3 -m venv venv`
- `source venv/bin/activate`
- `pip install groq`
- `pip install ollama`
- `export GROQ_API_KEY="<your groq api key>"`
- `export FAST_OLLAMA_MODEL="<your ideal Ollama model>"`

To run it:

- `./aicommit.py`
