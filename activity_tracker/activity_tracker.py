import argparse
import time
from typing import Dict, Any
import os
import pyaudio
import wave
import speech_recognition as sr
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich import print as rprint
from rich.text import Text
from rich.table import Table
from rich.style import Style
import datetime

import re
import ollama
from groq import Groq

console = Console()

ASCII_ART = """
 █████╗  ██████╗████████╗██╗██╗   ██╗██╗████████╗██╗   ██╗
██╔══██╗██╔════╝╚══██╔══╝██║██║   ██║██║╚══██╔══╝╚██╗ ██╔╝
███████║██║        ██║   ██║██║   ██║██║   ██║    ╚████╔╝ 
██╔══██║██║        ██║   ██║╚██╗ ██╔╝██║   ██║     ╚██╔╝  
██║  ██║╚██████╗   ██║   ██║ ╚████╔╝ ██║   ██║      ██║   
╚═╝  ╚═╝ ╚═════╝   ╚═╝   ╚═╝  ╚═══╝  ╚═╝   ╚═╝      ╚═╝   

████████╗██████╗  █████╗  ██████╗██╗  ██╗███████╗██████╗ 
╚══██╔══╝██╔══██╗██╔══██╗██╔════╝██║ ██╔╝██╔════╝██╔══██╗
   ██║   ██████╔╝███████║██║     █████╔╝ █████╗  ██████╔╝
   ██║   ██╔══██╗██╔══██║██║     ██╔═██╗ ██╔══╝  ██╔══██╗
   ██║   ██║  ██║██║  ██║╚██████╗██║  ██╗███████╗██║  ██║
   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
"""

# Default Obsidian vault path - replace with your actual path
DEFAULT_VAULT_PATH = "/Users/mike/Documents/obs-test/TEST"
# DEFAULT_VAULT_PATH = "/path/to/your/obsidian/vault"


def get_daily_file_path(vault_path):
    today = datetime.date.today()
    file_name = f"{today.strftime('%Y-%m-%d')}.md"
    return os.path.join(vault_path, "Time", "Tracker", file_name)


def ensure_daily_file_exists(file_path):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    if not os.path.exists(file_path):
        with open(file_path, "w") as f:
            f.write(
                f"# Activity Tracker: {datetime.date.today()}\n\n## Summary\n\n## Activities\n\n## Insights\n"
            )


def append_activity_to_file(file_path, activity, category, start_time, duration):
    with open(file_path, "r+") as f:
        content = f.read()
        activities_index = content.index("## Activities")
        insights_index = content.index("## Insights")

        # Extract and clean up existing activities
        activities_content = content[activities_index + 13 : insights_index].strip()
        activities_list = [
            line.strip() for line in activities_content.split("\n") if line.strip()
        ]

        # Format and add the new activity
        new_activity = f"- [{start_time.strftime('%H:%M')}] {activity} (Category: {category}) - {duration:.2f}s"
        activities_list.append(new_activity)

        # Join all activities with a single newline between them
        updated_activities = "\n".join(activities_list)

        # Construct the new content
        new_content = (
            content[:activities_index]
            + "## Activities\n\n"
            + updated_activities
            + "\n\n"
            + content[insights_index:]
        )

        f.seek(0)
        f.write(new_content)
        f.truncate()


def update_summary(file_path, activities):
    total_activities = len(activities)
    total_time = sum(activity["duration"] for activity in activities.values())

    with open(file_path, "r+") as f:
        content = f.read()
        summary_index = content.index("## Summary")
        activities_index = content.index("## Activities")

        new_content = (
            content[:summary_index]
            + f"## Summary\nTotal activities: {total_activities}\nTotal time tracked: {format_duration(total_time)}\n\n"
        )
        new_content += content[activities_index:]

        f.seek(0)
        f.write(new_content)
        f.truncate()


def update_insights(file_path, insights):
    with open(file_path, "r+") as f:
        content = f.read()
        insights_index = content.index("## Insights")

        new_content = content[:insights_index] + f"## Insights\n{insights}\n"

        f.seek(0)
        f.write(new_content)
        f.truncate()


def read_activities_from_file(file_path):
    activities = {}
    with open(file_path, "r") as f:
        for line in f:
            if line.startswith("- ["):
                match = re.match(
                    r"- \[(\d{2}:\d{2})\] (.*?) \(Category: (.*?)\) - (\d+\.\d+)s", line
                )
                if match:
                    time_str, activity, category, duration = match.groups()
                    start_time = datetime.datetime.strptime(time_str, "%H:%M").time()
                    activities[activity] = {
                        "category": category,
                        "start_time": start_time,
                        "duration": float(duration),
                    }
    return activities


def format_duration(seconds):
    hours, remainder = divmod(int(seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"


class AIService:
    def __init__(self, service_type: str):
        self.service_type = service_type

    def query(self, prompt: str, max_retries: int = 3) -> str:
        retries = 0
        while retries < max_retries:
            try:
                if self.service_type == "ollama":
                    return self.query_ollama(prompt)
                elif self.service_type == "groq":
                    return self.query_groq(prompt)
                else:
                    raise ValueError(f"Unsupported AI service: {self.service_type}")
            except Exception as e:  # Use a generic Exception
                retries += 1
                if retries == max_retries:
                    console.print(
                        f"[red]Error: Unable to complete the request after {max_retries} attempts.[/red]"
                    )
                    console.print(f"[yellow]Error details: {str(e)}[/yellow]")
                    console.print(
                        "[yellow]The process will continue with a default response.[/yellow]"
                    )
                    return (
                        "Uncategorized"
                        if "Categorize" in prompt
                        else "No insights available"
                    )
                else:
                    wait_time = 2**retries  # Exponential backoff
                    console.print(
                        f"[yellow]API error occurred. Retrying in {wait_time} seconds...[/yellow]"
                    )
                    time.sleep(wait_time)

    def query_ollama(self, prompt: str) -> str:
        response = ollama.generate(model="llama3.1", prompt=prompt)
        return response["response"]

    def query_groq(self, prompt: str) -> str:
        try:
            client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.1-70b-versatile",
            )
            return chat_completion.choices[0].message.content
        except Exception as e:  # Use a generic Exception
            console.print(f"[red]Groq API Error: {str(e)}[/red]")
            raise


class VoiceInputModule:
    @staticmethod
    def record_audio(duration=5):
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 44100
        RECORD_SECONDS = duration
        WAVE_OUTPUT_FILENAME = "temp_audio.wav"

        p = pyaudio.PyAudio()

        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK,
        )

        frames = []

        for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
            data = stream.read(CHUNK)
            frames.append(data)

        stream.stop_stream()
        stream.close()
        p.terminate()

        wf = wave.open(WAVE_OUTPUT_FILENAME, "wb")
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b"".join(frames))
        wf.close()

        return WAVE_OUTPUT_FILENAME

    @staticmethod
    def get_voice_input() -> str:
        audio_file = VoiceInputModule.record_audio()
        r = sr.Recognizer()
        with sr.AudioFile(audio_file) as source:
            audio = r.record(source)
        try:
            text = r.recognize_google(audio)
            os.remove(audio_file)
            return text
        except sr.UnknownValueError:
            os.remove(audio_file)
            return ""
        except sr.RequestError as e:
            os.remove(audio_file)
            return ""


class ActivityTracker:
    def __init__(self, ai_service: AIService, use_voice: bool, vault_path: str):
        self.ai_service = ai_service
        self.use_voice = use_voice
        self.vault_path = vault_path
        self.current_activity = None
        self.file_path = get_daily_file_path(self.vault_path)
        ensure_daily_file_exists(self.file_path)

    def toggle_activity(self):
        if self.current_activity:
            self.stop_activity()
        else:
            self.start_activity()

    def start_activity(self, activity_description: str) -> str:
        category_prompt = f"You are a world-class categorizer. You are part of a larger system where you play an important role. You only respond with one word or risk breaking the system. Categorize this activity: {activity_description}"
        category = self.ai_service.query(category_prompt)
        start_time = datetime.datetime.now()
        self.current_activity = {
            "description": activity_description,
            "category": category,
            "start_time": start_time,
        }
        return f"Activity started: {activity_description} ({category})"

    def stop_activity(self) -> str:
        if not self.current_activity:
            return "No active activity to stop."

        end_time = datetime.datetime.now()
        duration = (end_time - self.current_activity["start_time"]).total_seconds()

        append_activity_to_file(
            self.file_path,
            self.current_activity["description"],
            self.current_activity["category"],
            self.current_activity["start_time"],
            duration,
        )

        # Update the summary after appending the activity
        activities = read_activities_from_file(self.file_path)
        update_summary(self.file_path, activities)

        result = (
            f"Activity stopped: {self.current_activity['description']} "
            f"({self.current_activity['category']}) - "
            f"Duration: {format_duration(duration)}"
        )

        self.current_activity = None
        return result

    def show_stats(self):
        activities = read_activities_from_file(self.file_path)
        if not activities:
            rprint("[yellow]No activities recorded yet.[/yellow]")
            return

        stats = Panel(
            "\n".join(
                [
                    f"{act}: {format_duration(data['duration'])} ({data['category']})"
                    for act, data in activities.items()
                ]
            ),
            title="Activity Statistics",
            expand=False,
            border_style="purple",
        )
        console.print(stats)

        insights_prompt = f"""Based on these activities (durations are in seconds):
        {', '.join([f"{act}: {data['duration']}s ({data['category']})" for act, data in activities.items()])}
        Provide 1-3 concise insights about time usage and productivity. Focus only on the given activities and durations.
        Remember that durations are in seconds, not minutes. Do not give general health advice or suggestions not directly related to the data provided."""
        insights = self.ai_service.query(insights_prompt)
        rprint(f"\n[purple]Insights:[/purple]\n{insights}")

        # Update the markdown file with new insights
        update_insights(self.file_path, insights)


def display_menu(tracker):
    menu = Table.grid(padding=(0, 1))
    menu.add_column(style="blue", justify="left")
    menu.add_column(style="white", justify="left")

    if tracker.current_activity:
        menu.add_row("1", "Stop activity")
        status = Text(
            f"Currently tracking: {tracker.current_activity['description']}",
            style="green",
        )
        duration = (
            datetime.datetime.now() - tracker.current_activity["start_time"]
        ).total_seconds()
    else:
        menu.add_row("1", "Start activity")
        status = Text("No activity in progress", style="red")

    menu.add_row("2", "Show stats")
    menu.add_row("3", "Exit")

    content = Table.grid(padding=1)
    content.add_row(status)
    content.add_row(menu)

    return Panel(
        content,
        title="Activity Tracker",
        border_style="blue",
        expand=False,
        padding=(1, 1),
    )


def main():
    parser = argparse.ArgumentParser(
        description="Activity Tracker with AI-powered insights and Obsidian integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Run with default settings:
    python script.py

  Use Ollama AI service with voice input:
    python script.py --ai-service ollama --voice

  Specify a custom Obsidian vault path:
    python script.py --vault-path /path/to/your/obsidian/vault

  Full example with all options:
    python script.py --ai-service groq --voice --vault-path /path/to/your/obsidian/vault
        """,
    )
    parser.add_argument(
        "--ai-service",
        choices=["groq", "ollama"],
        default="groq",
        help="AI service to use for categorization and insights (default: groq)",
    )
    parser.add_argument(
        "--voice",
        action="store_true",
        help="Use voice input for activities instead of text input",
    )
    parser.add_argument(
        "--vault-path",
        default=DEFAULT_VAULT_PATH,
        help=f"Path to Obsidian vault (default: {DEFAULT_VAULT_PATH})",
    )
    args = parser.parse_args()

    ai_service = AIService(args.ai_service)
    tracker = ActivityTracker(ai_service, args.voice, args.vault_path)

    console.print(Text(ASCII_ART, style="purple"))

    while True:
        console.print()  # Add an empty line for spacing
        console.print(display_menu(tracker))

        choice = console.input("[blue]Choose an option: [/blue]")
        console.print()  # Add an empty line for spacing

        if choice == "1":
            if tracker.current_activity:
                console.print("[blue]Stopping activity...[/blue]")
                result = tracker.stop_activity()
            else:
                console.print("[blue]Please describe your activity...[/blue]")
                if tracker.use_voice:
                    console.print("[white]Recording...[/white]")
                    activity_description = VoiceInputModule.get_voice_input()
                    if activity_description:
                        console.print("[blue]Recording finished.[/blue]")
                    else:
                        console.print(
                            "[red]Could not understand audio. Please try again.[/red]"
                        )
                        continue
                else:
                    activity_description = console.input(
                        "[blue]Enter activity description: [/blue]"
                    )
                result = tracker.start_activity(activity_description)

            if result:
                console.print(f"[white]{result}[/white]")
            else:
                console.print("[red]Failed to start/stop activity.[/red]")
        elif choice == "2":
            tracker.show_stats()
        elif choice == "3":
            console.print("[purple]Exiting Activity Tracker. Goodbye![/purple]")
            break
        else:
            console.print("[red]Invalid option. Please try again.[/red]")


if __name__ == "__main__":
    main()
