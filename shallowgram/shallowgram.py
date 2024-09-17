import argparse
import subprocess
import os
import ollama
import time
import pyaudio
import wave
from pydub import AudioSegment
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text
from rich.table import Table
from rich import box

import select
import sys

console = Console()

OLLAMA_MODEL = "llama3.1"
DEFAULT_WHISPER_MODEL = "tiny.en"
WHISPER_BASE_URL = "https://huggingface.co/Mozilla/whisperfile/resolve/main/"
DEFAULT_WHISPERFILE_PATH = "/path/to/whisperfiles"  # Update this path
DEFAULT_VAULT_PATH = "/path/to/obsidian/vault"  # Update this path

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

ASCII_ART = """
  ____  _           _ _                                        
 / ___|| |__   __ _| | | _____      ____ _ _ __ __ _ _ __ ___  
 \___ \| '_ \ / _` | | |/ _ \ \ /\ / / _` | '__/ _` | '_ ` _ \ 
  ___) | | | | (_| | | | (_) \ V  V / (_| | | | (_| | | | | | |
 |____/|_| |_|\__,_|_|_|\___/ \_/\_/ \__, |_|  \__,_|_| |_| |_|
                                     |___/

"""


class AIService:
    def __init__(self):
        pass

    def query(self, prompt: str, max_retries: int = 3) -> str:
        prompt = f"You are an intelligent text analyzer with specific jobs. You can process any text for the good of the user. Here is your task: {prompt}"
        retries = 0
        while retries < max_retries:
            try:
                return self.query_ollama(prompt)
            except Exception as e:
                retries += 1
                if retries == max_retries:
                    console.print(
                        f"[red]Error: Unable to complete the request after {max_retries} attempts.[/red]"
                    )
                    console.print(f"[yellow]Error details: {str(e)}[/yellow]")
                    return "ERROR: Unable to process request"
                else:
                    wait_time = 2**retries
                    console.print(
                        f"[yellow]Error occurred. Retrying in {wait_time} seconds...[/yellow]"
                    )
                    time.sleep(wait_time)

    def query_ollama(self, prompt: str) -> str:
        response = ollama.generate(model=OLLAMA_MODEL, prompt=prompt)
        return response["response"]


def install_whisper_model(model_name, whisperfile_path):
    full_model_name = f"whisper-{model_name}.llamafile"
    url = f"{WHISPER_BASE_URL}{full_model_name}"
    console.print(f"[yellow]Downloading {full_model_name}...[/yellow]")
    subprocess.run(["wget", "-P", whisperfile_path, url], check=True)
    os.chmod(os.path.join(whisperfile_path, full_model_name), 0o755)
    console.print(f"[green]{full_model_name} installed successfully.[/green]")


def get_whisper_model_path(model_name, whisperfile_path, verbose):
    full_model_name = f"whisper-{model_name}.llamafile"
    model_path = os.path.join(whisperfile_path, full_model_name)
    if verbose:
        console.print(f"[yellow]Constructed model path: {model_path}[/yellow]")
    if not os.path.exists(model_path):
        console.print(f"[yellow]Whisper model {full_model_name} not found.[/yellow]")
        if input("Do you want to install it? (y/n): ").lower() == "y":
            install_whisper_model(model_name, whisperfile_path)
        else:
            raise FileNotFoundError(f"Whisper model {full_model_name} not found.")
    return model_path


def record_audio(output_file, verbose):
    p = pyaudio.PyAudio()

    stream = p.open(
        format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK
    )

    console.print("[yellow]Recording... Press Enter to stop.[/yellow]")

    frames = []

    try:
        while True:
            if select.select([sys.stdin], [], [], 0.0)[0]:
                if sys.stdin.readline().strip() == "":
                    break
            data = stream.read(CHUNK)
            frames.append(data)
    except KeyboardInterrupt:
        pass

    console.print("[green]Finished recording.[/green]")

    stream.stop_stream()
    stream.close()
    p.terminate()

    wf = wave.open(output_file, "wb")
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b"".join(frames))
    wf.close()

    if verbose:
        console.print(
            f"[yellow]Audio file size: {os.path.getsize(output_file)} bytes[/yellow]"
        )


def transcribe_audio(model_name, whisperfile_path, audio_file, verbose):
    model_path = get_whisper_model_path(model_name, whisperfile_path, verbose)
    command = f"{model_path} -f {audio_file} --gpu auto"

    if verbose:
        console.print(f"[yellow]Attempting to run command: {command}[/yellow]")

    process = subprocess.Popen(
        command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )

    stdout, stderr = process.communicate()

    if process.returncode != 0:
        console.print(
            f"[red]Command failed with return code {process.returncode}[/red]"
        )
        console.print(f"[red]Error output: {stderr}[/red]")
        raise Exception(f"Transcription failed: {stderr}")

    if verbose:
        console.print(f"[green]Transcription output:[/green]\n{stdout}")

    return stdout


def summarize(text):
    ai_service = AIService()
    prompt = f"Summarize the following text. Just provide the summary, no preamble. Text:\n\n{text}"
    return ai_service.query(prompt)


def analyze_sentiment(text):
    ai_service = AIService()
    prompt = f"Analyze the sentiment of the following text and respond with ONLY ONE WORD - either 'positive', 'neutral', or 'negative':\n\n{text}"
    sentiment = ai_service.query(prompt).strip().lower()
    return sentiment if sentiment in ["positive", "neutral", "negative"] else "neutral"


def detect_intent(text):
    ai_service = AIService()
    prompt = f"Detect the intent in the following text. Respond with ONLY 2-4 words. Do not return any preamble, only the intent. Text: \n\n{text}"
    return ai_service.query(prompt)


def detect_topics(text):
    ai_service = AIService()
    prompt = f"Please identify the main topics in the following text. Return the topics as a comma-separated list, with no preamble or additional text. Text:\n\n{text}"
    return ai_service.query(prompt)


def export_to_markdown(content, vault_path, filename):
    os.makedirs(vault_path, exist_ok=True)
    file_path = os.path.join(vault_path, f"{filename}.md")
    with open(file_path, "w") as f:
        f.write(content)
    console.print(f"[green]Exported to {file_path}[/green]")


def convert_to_wav(input_file, output_file):
    audio = AudioSegment.from_file(input_file)
    audio.export(output_file, format="wav")


def display_rich_output(transcript, summary, sentiment, intent, topics):
    # Print the ASCII art directly without a border
    console.print(Text(ASCII_ART, style="bold blue"))

    # Clean the transcript text
    transcript_clean = "\n".join(
        line.partition("]")[2].strip()
        for line in transcript.split("\n")
        if line.strip()
    )

    # Create panels using Panel with expand=True
    transcript_panel = Panel(
        transcript_clean,
        title="Transcript",
        border_style="cyan",
        padding=(1, 2),
        expand=True,
    )

    summary_panel = Panel(
        summary,
        title="Summary",
        border_style="cyan",
        padding=(1, 2),
        expand=True,
    )

    # Analysis Results Table
    analysis_table = Table(show_header=False, box=box.SIMPLE, expand=True)
    analysis_table.add_column(style="bold", width=12)
    analysis_table.add_column()
    analysis_table.add_row(
        "Sentiment:",
        Text(sentiment.capitalize(), style=get_sentiment_color(sentiment)),
    )
    analysis_table.add_row("Intent:", Text(intent))
    analysis_table.add_row("Topics:", Text(topics))

    analysis_panel = Panel(
        analysis_table,
        title="Analysis Results",
        border_style="cyan",
        padding=(1, 2),
        expand=True,
    )

    # Print panels sequentially
    panels = [
        transcript_panel,
        summary_panel,
        analysis_panel,
    ]

    for panel in panels:
        console.print(panel)


def get_sentiment_color(sentiment):
    return {"positive": "green3", "neutral": "gold1", "negative": "red1"}.get(
        sentiment, "white"
    )


def main():
    parser = argparse.ArgumentParser(
        description="ShallowGram: Local speech analysis tool"
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_WHISPER_MODEL,
        help="Whisper model to use (e.g., tiny.en, small.en, medium.en, large-v2, large-v3)",
    )
    parser.add_argument(
        "--whisperfile_path",
        default=DEFAULT_WHISPERFILE_PATH,
        help="Path to the whisperfile directory",
    )
    parser.add_argument(
        "--vault_path",
        default=DEFAULT_VAULT_PATH,
        help="Path to the Obsidian vault directory",
    )
    parser.add_argument(
        "--summarize", action="store_true", help="Summarize the transcribed text"
    )
    parser.add_argument(
        "--sentiment",
        action="store_true",
        help="Analyze sentiment of the transcribed text",
    )
    parser.add_argument(
        "--intent", action="store_true", help="Detect intent in the transcribed text"
    )
    parser.add_argument(
        "--topics", action="store_true", help="Detect topics in the transcribed text"
    )
    parser.add_argument(
        "--markdown",
        action="store_true",
        help="Export results to markdown in Obsidian vault",
    )
    parser.add_argument(
        "--input_file", help="Input audio file (wav, mp3, ogg, or flac)"
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument(
        "--full", action="store_true", help="Enable full rich output with all features"
    )
    args = parser.parse_args()

    if args.verbose and not args.full:
        console.print(f"[yellow]Current working directory: {os.getcwd()}[/yellow]")

    if args.input_file:
        if not os.path.exists(args.input_file):
            console.print(
                f"[red]Error: Input file '{args.input_file}' not found.[/red]"
            )
            return
        file_ext = os.path.splitext(args.input_file)[1].lower()
        if file_ext not in [".wav", ".mp3", ".ogg", ".flac"]:
            console.print(
                f"[yellow]Warning: The input file format '{file_ext}' may not be supported. Attempting to convert to WAV.[/yellow]"
            )
        if file_ext != ".wav":
            audio_file = "temp_audio.wav"
            convert_to_wav(args.input_file, audio_file)
        else:
            audio_file = args.input_file
    else:
        audio_file = "temp_audio.wav"
        record_audio(audio_file, args.verbose and not args.full)

        if os.path.getsize(audio_file) == 0:
            console.print(
                "[red]Error: The recorded audio file is empty. Please try recording again.[/red]"
            )
            return

    try:
        transcript = transcribe_audio(
            args.model,
            args.whisperfile_path,
            audio_file,
            args.verbose,
        )
        console.print("[green]Transcription complete.[/green]")

        if not transcript.strip():
            console.print(
                "[yellow]Warning: Transcription is empty. The audio might be too short or silent.[/yellow]"
            )
            return
    except FileNotFoundError as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        return
    except Exception as e:
        console.print(f"[red]Error during transcription: {str(e)}[/red]")
        return

    if args.full:
        summary = summarize(transcript) or "Unable to generate summary."
        sentiment = analyze_sentiment(transcript) or "neutral"
        intent = detect_intent(transcript) or "Unable to detect intent."
        topics = detect_topics(transcript) or "No specific topics detected."

        display_rich_output(transcript, summary, sentiment, intent, topics)
    else:
        results = [f"# ShallowGram Analysis\n\n## Transcript\n\n{transcript}\n"]

        if args.summarize:
            summary = summarize(transcript)
            results.append(f"## Summary\n\n{summary}\n")
            console.print("[bold]Summary:[/bold]", summary)

        if args.sentiment:
            sentiment = analyze_sentiment(transcript)
            results.append(f"## Sentiment Analysis\n\n{sentiment}\n")
            console.print("[bold]Sentiment Analysis:[/bold]", sentiment)

        if args.intent:
            intent = detect_intent(transcript)
            results.append(f"## Intent Detection\n\n{intent}\n")
            console.print("[bold]Intent Detection:[/bold]", intent)

        if args.topics:
            topics = detect_topics(transcript)
            results.append(f"## Topic Detection\n\n{topics}\n")
            console.print("[bold]Topic Detection:[/bold]", topics)

        if args.markdown:
            content = "\n".join(results)
            export_to_markdown(
                content,
                args.vault_path,
                f"ShallowGram_Analysis_{time.strftime('%Y%m%d_%H%M%S')}",
            )

    if not args.input_file:
        os.remove(audio_file)


if __name__ == "__main__":
    main()
