# Research Assistant

An AI-powered tool to assist with research queries using multiple sources and LLMs.

## Installation

1. Navigate to the `research_assistant` directory
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
3. Set up environment variables:
   - `EXA_API_KEY`: Your Exa API key (required)
   - `GROQ_API_KEY`: Your Groq API key (if using Groq)
   - `ANTHROPIC_API_KEY`: Your Anthropic API key (if using Anthropic)
   - `OLLAMA_MODEL`: Your preferred Ollama model (default is "llama3.1")

## Usage

```
python research_assistant.py [options] "Your research query"
```

### Options

- `--service {ollama,groq,anthropic}`: AI service to use (default: ollama)
- `--model MODEL`: Specify a custom model to use (optional)
- `--num_results N`: Total number of results to fetch (default: 6)
- `--output DIR`: Output directory name (default: research_results)
- `--technical`: Use technical mode (include arXiv results)
- `--vault_path PATH`: Path to the Obsidian vault directory (default: path/to/vault)
- `--firecrawl_url URL`: Base URL for the Firecrawl service (default: http://localhost:3002)

### Examples

```
python research_assistant.py "Impact of climate change on biodiversity"
python research_assistant.py --service groq --num_results 10 "Quantum computing applications"
python research_assistant.py --technical --output quantum_research "Recent advancements in quantum entanglement"
```

## Features

- Multi-source research: Exa, arXiv (for technical queries), and web scraping via Firecrawl
- AI-powered summarization and content generation
- Supports multiple LLM services: Ollama, Groq, and Anthropic
- Creates comprehensive learning materials
- Organizes results into markdown files for easy integration with note-taking systems

## Output

The script generates several markdown files in the specified output directory within the vault path:

1. `exa_results.md`: Summary of Exa search results
2. `arxiv_results.md`: Summary of arXiv results (if technical mode is used)
3. `firecrawl_result_X.md`: Individual results from web scraping
4. `summary.md`: Comprehensive learning material synthesized from all sources

## Notes

- Ensure you have the necessary API keys set up as environment variables
- For technical queries, results are split between Exa and arXiv
- The Firecrawl service should be running and accessible at the specified URL
- Output files are saved in `[vault_path]/[output_directory]`
