# automations

A collection of community created scripts to automate your life

## AI Commit

Use LLMs to generate your commit messages.

### Installation

on windows powershell:
- `git clone https://github.com/MikeBirdTech/automations.git && cd automations`
- `python -m venv venv`
- `./venv/Scripts/activate`
- `pip install groq`
- `pip install ollama`
- `$Env:GROQ_API_KEY="<your groq api key>"`
- `$Env:FAST_OLLAMA_MODEL="<your ideal Ollama model>"`
how to run it:
- `python ./aicommit.py --groq`

Requires

- `pip install groq`
- `pip install ollama`
- set `GROQ_API_KEY`
- set `FAST_OLLAMA_MODEL` to your ideal Ollama model

Options

- Local by default
- Use Groq with `--groq`
- Arrow keys by default
- Use Vim keys with `--vim`
- Use number selection with `--num`
