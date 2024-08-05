# Windows Instructions

How to run the scripts on windows

## AI Commit

in Windows Powershell:

- `git clone https://github.com/MikeBirdTech/automations.git && cd automations`
- `python -m venv venv`
- `./venv/Scripts/activate`
- `pip install groq`
- `pip install ollama`
- `$Env:GROQ_API_KEY="<your groq api key>"`
- `$Env:FAST_OLLAMA_MODEL="<your ideal Ollama model>"`

To run it:

- `python ./aicommit.py --groq`
