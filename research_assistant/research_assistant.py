#!/usr/bin/env python
import argparse
import io
import os
import re
import sys
import time
from typing import List, Dict
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

import anthropic
from bs4 import BeautifulSoup
from exa_py import Exa
from groq import Groq
import ollama
import PyPDF2
import requests

# Default values and constants
DEFAULT_VAULT_PATH = "path/to/vault"
DEFAULT_FIRECRAWL_BASE_URL = "http://localhost:3002"
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")
GROQ_MODEL = "llama-3.1-70b-versatile"
ANTHROPIC_MODEL = "claude-3-5-sonnet-20240620"

# Exa search configuration
EXCLUDED_DOMAINS = [
    "twitter.com",
    "facebook.com",
    "x.com",
    "reddit.com",
    "github.com",
    "linkedin.com",
]
START_PUBLISHED_DATE = "2021-01-01"


class AIService:
    def __init__(self, service_type: str, model: str = None):
        self.service_type = service_type
        self.model = model

    def query(self, prompt: str, model: str = None) -> str:
        if self.service_type == "ollama":
            return self.query_ollama(prompt)
        elif self.service_type == "groq":
            return self.query_groq(prompt)
        elif self.service_type == "anthropic":
            return self.query_anthropic(prompt)
        else:
            raise ValueError(f"Unsupported AI service: {self.service_type}")

    def query_ollama(self, prompt: str) -> str:
        try:
            print("Generating research insights...", end="", flush=True)
            response = ollama.generate(
                model=self.model or OLLAMA_MODEL,
                prompt=prompt,
                system="You are a research assistant specialized in synthesizing information and providing comprehensive insights.",
                options={
                    "num_predict": 1000,
                },
                keep_alive="2m",
            )
            print("Done!")
            return response["response"]
        except Exception as e:
            print(f"\nError querying Ollama: {e}")
            sys.exit(1)

    def query_groq(self, prompt: str) -> str:
        try:
            client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant specializing in research and information synthesis.",
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                model=self.model or GROQ_MODEL,
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            print(f"\nError querying Groq: {e}")
            sys.exit(1)

    def query_anthropic(self, prompt: str) -> str:
        try:
            client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
            message = client.messages.create(
                model=self.model or ANTHROPIC_MODEL,
                max_tokens=1000,
                messages=[
                    {"role": "user", "content": prompt},
                ],
            )
            return message.content[0].text
        except Exception as e:
            print(f"Error querying Anthropic: {e}")
            sys.exit(1)


class ResearchAssistant:
    def __init__(
        self,
        service_type: str,
        model: str = None,
        vault_path: str = DEFAULT_VAULT_PATH,
        firecrawl_base_url: str = DEFAULT_FIRECRAWL_BASE_URL,
    ):
        self.ai_service = AIService(service_type, model)
        self.model = model
        self.exa_client = Exa(api_key=os.environ["EXA_API_KEY"])
        self.firecrawl_base_url = firecrawl_base_url
        self.vault_path = vault_path

    def search_exa(self, query: str, num_results: int = 3) -> List[Dict]:
        try:
            search_response = self.exa_client.search_and_contents(
                query,
                type="auto",
                use_autoprompt=True,
                num_results=num_results,
                text={"include_html_tags": False, "max_characters": 2000},
                summary=True,
                exclude_domains=EXCLUDED_DOMAINS,
                start_published_date=START_PUBLISHED_DATE,
            )
            print(
                f"Exa search successful. Found {len(search_response.results)} results."
            )

            results = []
            for result in search_response.results:
                result_dict = {
                    "title": result.title if hasattr(result, "title") else "N/A",
                    "url": result.url if hasattr(result, "url") else "N/A",
                    "summary": (
                        result.text[:500] + "..." if hasattr(result, "text") else "N/A"
                    ),
                    "highlights": (
                        result.highlights if hasattr(result, "highlights") else []
                    ),
                }
                results.append(result_dict)

            return results
        except Exception as e:
            print(f"Error in Exa search: {e}")
            return []

    def search_arxiv(self, query: str, max_results: int = 5) -> List[Dict]:
        print(f"Searching arXiv for: {query}")
        encoded_query = urllib.parse.quote(query)
        url = f"http://export.arxiv.org/api/query?search_query=all:{encoded_query}&start=0&max_results={max_results}"

        with urllib.request.urlopen(url) as response:
            xml_data = response.read()

        root = ET.fromstring(xml_data)
        namespace = {"atom": "http://www.w3.org/2005/Atom"}

        results = []
        for entry in root.findall("atom:entry", namespace):
            title = entry.find("atom:title", namespace).text
            summary = entry.find("atom:summary", namespace).text
            arxiv_id = entry.find("atom:id", namespace).text.split("/abs/")[-1]
            pdf_url = f"http://arxiv.org/pdf/{arxiv_id}.pdf"

            full_text = self.get_pdf_text(pdf_url)

            results.append(
                {
                    "title": title,
                    "summary": summary,
                    "url": f"http://arxiv.org/abs/{arxiv_id}",
                    "full_text": full_text,
                }
            )

            # Respect arXiv's rate limit
            time.sleep(3)

        print(f"Found and processed {len(results)} arXiv results.")
        return results

    def get_pdf_text(self, pdf_url: str) -> str:
        try:
            response = requests.get(pdf_url)
            response.raise_for_status()

            with io.BytesIO(response.content) as open_pdf_file:
                read_pdf = PyPDF2.PdfReader(open_pdf_file)
                text = ""
                for page in read_pdf.pages:
                    text += page.extract_text()

            return text
        except Exception as e:
            print(f"Error downloading or processing PDF from {pdf_url}: {str(e)}")
            return ""

    def firecrawl_extract(self, urls: List[str]) -> List[Dict]:
        results = []
        for url in urls:
            print(f"Extracting data from {url} using Firecrawl...")
            try:
                response = requests.post(
                    f"{self.firecrawl_base_url}/v0/scrape",
                    json={"url": url},
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
                data = response.json()
                content = data.get("data", {}).get("markdown", "N/A")
                cleaned_content = self.clean_content(content)
                results.append(
                    {
                        "url": url,
                        "content": cleaned_content,
                        "title": data.get("data", {})
                        .get("metadata", {})
                        .get("title", "N/A"),
                    }
                )
                print(f"Successfully extracted and cleaned data from {url}")
            except requests.RequestException as e:
                print(f"Error extracting data from {url}: {e}")
        return results

    def clean_content(self, content: str) -> str:
        # Remove HTML tags
        soup = BeautifulSoup(content, "html.parser")
        text = soup.get_text()

        # Remove URLs
        text = re.sub(r"http\S+", "", text)

        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text).strip()

        # Remove non-alphanumeric characters except punctuation
        text = re.sub(r"[^a-zA-Z0-9\s.,!?-]", "", text)

        return text

    def create_markdown_files(
        self,
        output_dir: str,
        query: str,
        exa_results: List[Dict],
        arxiv_results: List[Dict],
        firecrawl_results: List[Dict],
        technical: bool,
    ):
        # Create Exa results file
        with open(os.path.join(output_dir, "exa_results.md"), "w") as f:
            f.write(f"# Exa Search Results for Query: {query}\n\n")
            for i, result in enumerate(exa_results, 1):
                f.write(f"## Result {i}\n")
                f.write(f"### Title: {result.get('title', 'N/A')}\n")
                f.write(f"### URL: {result.get('url', 'N/A')}\n")
                f.write(f"### Summary:\n{result.get('summary', 'N/A')}\n\n")

                highlights = result.get("highlights")
                if highlights and isinstance(highlights, list):
                    f.write("### Highlights:\n")
                    for highlight in highlights:
                        f.write(f"- {highlight}\n")
                    f.write("\n")

                f.write("\n\n---\n\n")

        print(f"Created exa_results.md with {len(exa_results)} results.")

        # Create arXiv results file (if technical)
        if technical:
            with open(os.path.join(output_dir, "arxiv_results.md"), "w") as f:
                f.write(f"# arXiv Search Results for Query: {query}\n\n")
                f.write(
                    "Thank you to arXiv for use of its open access interoperability.\n\n"
                )
                for i, result in enumerate(arxiv_results, 1):
                    f.write(f"## Result {i}\n")
                    f.write(f"- Title: {result.get('title', 'N/A')}\n")
                    f.write(f"- URL: {result.get('url', 'N/A')}\n")
                    f.write(f"- Summary: {result.get('summary', 'N/A')}\n\n")

            print(f"Created arxiv_results.md with {len(arxiv_results)} results.")

        # Create individual Firecrawl result files (unchanged)
        for i, result in enumerate(firecrawl_results, 1):
            with open(os.path.join(output_dir, f"firecrawl_result_{i}.md"), "w") as f:
                f.write(f"# Firecrawl Result {i} for Query: {query}\n\n")
                f.write(f"- URL: {result.get('url', 'N/A')}\n")
                f.write(f"- Title: {result.get('title', 'N/A')}\n")
                f.write(f"- Content:\n\n{result.get('content', 'N/A')}\n")
            print(f"Created firecrawl_result_{i}.md")

    def summarize_single_source(
        self, query: str, source_content: str, source_type: str, source_url: str
    ) -> str:
        prompt = f"""
        Original Query: {query}

        Summarize the following {source_type} content in the context of the original query.
        Provide key points, any relevant statistics or findings, and general information that a researcher would care about in relation to the query.

        Content:
        {source_content}

        Source URL: {source_url}

        Your summary should be concise and highly factual, highlighting the most important information from this source that relates to the original query.
        Do not mention Firecrawl or any other tool used in the data collection process.
        """
        return self.ai_service.query(prompt, self.model)

    def create_comprehensive_learning_material(
        self,
        query: str,
        individual_summaries: List[str],
        exa_results: List[Dict],
        arxiv_results: List[Dict],
        technical: bool,
    ) -> str:

        # Combine full texts from arXiv results
        arxiv_full_texts = (
            "\n\n".join(
                [result["full_text"] for result in arxiv_results if result["full_text"]]
            )
            if technical
            else ""
        )

        combined_content = "\n\n".join(individual_summaries) + "\n\n" + arxiv_full_texts

        prompt = f"""
        Original Query: {query}
        Based on the following summaries of various sources, create comprehensive learning material on the topic. Your goal is to help someone learn this topic 90% faster than traditional research methods. Be thorough, accurate, and helpful. Do not hallucinate.

        Source Summaries:
        {combined_content}

        Your response should include:

        1. An executive summary (3-5 sentences)
        2. Key concepts and their explanations
        3. A detailed outline with main points and sub-points
        4. Expert opinions or consensus (if any)
        5. Real-world applications or examples
        6. Relevant quotes or statistics from the sources (use only real, retrieved information)
        7. Common misconceptions or challenges in understanding this topic
        8. A short list of critical questions to explore for a deeper understanding
        9. A suggested learning path or study guide
        10. A list of the most relevant sources for further reading (use only the provided Exa and arXiv results)

        Ensure that your material is comprehensive, well-structured, and based solely on the provided information.
        Do not generate any fictional sources or information. Truth is the most important thing.
        Use clear headings and subheadings to organize the information.
        """

        ai_generated_content = self.ai_service.query(prompt, self.model)

        # Prepare source summaries for appending
        exa_summaries = "\n\n".join(
            [
                f"- [{result['title']}]({result['url']})\n  {result['summary']}"
                for result in exa_results
            ]
        )
        arxiv_summaries = "\n\n".join(
            [
                f"- [{result['title']}]({result['url']})\n  {result['summary']}"
                for result in arxiv_results
            ]
        )

        # Combine AI-generated content with source summaries
        final_output = f"""
# Comprehensive Learning Material

{ai_generated_content}

## Source Summaries

### Exa Search Results

{exa_summaries}
"""

        if technical:
            arxiv_summaries = "\n\n".join(
                [
                    f"- [{result['title']}]({result['url']})\n  {result['summary']}"
                    for result in arxiv_results
                ]
            )
            final_output += f"""

### arXiv Search Results

{arxiv_summaries}

Thank you to arXiv for use of its open access interoperability.
"""

        return final_output

    def process_query(
        self, query: str, num_results: int, output_dir: str, technical: bool
    ) -> str:
        full_output_dir = os.path.join(self.vault_path, output_dir)
        os.makedirs(full_output_dir, exist_ok=True)

        print("Searching Exa...")
        exa_results = self.search_exa(
            query, num_results if not technical else num_results // 2
        )

        arxiv_results = []
        if technical:
            print("Searching arXiv...")
            arxiv_results = self.search_arxiv(query, num_results // 2)

        if not exa_results and not arxiv_results:
            print("No results from Exa or arXiv search. Skipping Firecrawl extraction.")
            return "Research process completed with no results."

        print("Extracting data with Firecrawl...")
        urls = [result.get("url") for result in exa_results if result.get("url")]
        urls += [result.get("url") for result in arxiv_results if result.get("url")]
        firecrawl_results = self.firecrawl_extract(urls)

        print("Creating markdown files...")
        self.create_markdown_files(
            full_output_dir,
            query,
            exa_results,
            arxiv_results,
            firecrawl_results,
            technical,
        )

        print("Generating individual summaries...")
        individual_summaries = []
        for result in firecrawl_results:
            summary = self.summarize_single_source(
                query, result["content"], "Firecrawl", result["url"]
            )
            individual_summaries.append(summary)

        print("Generating comprehensive learning material...")
        learning_material = self.create_comprehensive_learning_material(
            query, individual_summaries, exa_results, arxiv_results, technical
        )

        # Save learning material
        with open(os.path.join(full_output_dir, "summary.md"), "w") as f:
            f.write(learning_material)
        print("Created Summary. Enjoy the learning!")

        return f"Research process completed. Files saved in {full_output_dir}"


def main():
    parser = argparse.ArgumentParser(description="Research Assistant")
    parser.add_argument(
        "--service",
        choices=["ollama", "groq", "anthropic"],
        default="ollama",
        help="AI service to use",
    )
    parser.add_argument("--model", help="Specify the model to use (optional)")
    parser.add_argument(
        "--num_results",
        type=int,
        default=6,
        help="Total number of results to fetch. If --technical is used, half will come from Exa and half from arXiv. Otherwise, all results will be from Exa.",
    )
    parser.add_argument(
        "--output", default="research_results", help="Output directory name"
    )
    parser.add_argument(
        "--technical",
        action="store_true",
        help="Use technical mode (include arXiv results)",
    )
    parser.add_argument(
        "--vault_path",
        default=DEFAULT_VAULT_PATH,
        help="Path to the vault directory",
    )
    parser.add_argument(
        "--firecrawl_url",
        default=DEFAULT_FIRECRAWL_BASE_URL,
        help="Base URL for the Firecrawl service",
    )
    parser.add_argument("query", help="Research query")
    args = parser.parse_args()

    try:
        if "EXA_API_KEY" not in os.environ:
            raise ValueError("EXA_API_KEY environment variable is not set")

        assistant = ResearchAssistant(
            args.service, args.model, args.vault_path, args.firecrawl_url
        )
        result = assistant.process_query(
            args.query, args.num_results, args.output, args.technical
        )
        print(result)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
