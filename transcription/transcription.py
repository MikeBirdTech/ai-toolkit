#!/usr/bin/env python

import argparse
import itertools
import os
import subprocess
import sys
import time

from faster_whisper import WhisperModel
from pyannote.audio import Pipeline
import torch


def simple_spinner():
    spinner = itertools.cycle(["🌑", "🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘"])
    while True:
        sys.stdout.write(next(spinner))
        sys.stdout.flush()
        sys.stdout.write("\b\b")
        time.sleep(0.1)


def extract_audio(video_file):
    print("Extracting audio from video...")
    output_dir = os.path.dirname(video_file)
    audio_file = os.path.join(output_dir, "temp_audio.wav")

    ffmpeg_cmd = [
        "ffmpeg",
        "-i",
        video_file,  # Input file
        "-vn",  # Disable video output
        "-acodec",
        "pcm_s16le",  # Set audio codec to PCM 16-bit little-endian
        "-ar",
        "44100",  # Set audio sampling rate to 44.1 kHz
        "-ac",
        "2",  # Set number of audio channels to 2 (stereo)
        audio_file,  # Output file
    ]

    try:
        result = subprocess.run(ffmpeg_cmd, check=True, capture_output=True, text=True)
        print(f"Audio extracted successfully: {audio_file}")
        return audio_file
    except subprocess.CalledProcessError as e:
        print(f"Error during audio extraction: {e}")
        print(f"FFmpeg error output: {e.stderr}")
        return None


def transcribe_and_diarize(
    audio_file, auth_token, model_size="large-v2", compute_type="float32"
):
    # Transcription
    print("Transcribing...")
    device = "cpu"  # Always use CPU for Whisper model
    model = WhisperModel(model_size, device=device, compute_type=compute_type)

    spinner = simple_spinner()
    try:
        segments, _ = model.transcribe(audio_file, word_timestamps=True)
        segments = list(segments)  # Convert generator to list
    finally:
        spinner.close()
    print("\rTranscription complete.")

    # Diarization
    print("Performing diarization...")
    diarization_pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1", use_auth_token=auth_token
    )
    if torch.cuda.is_available():
        diarization_pipeline = diarization_pipeline.to(torch.device("cuda"))
    elif torch.backends.mps.is_available():
        diarization_pipeline = diarization_pipeline.to(torch.device("mps"))
    diarization = diarization_pipeline(audio_file)

    # Combine transcription and diarization
    result = []
    for segment in segments:
        speaker = get_dominant_speaker(diarization, segment.start, segment.end)
        result.append(
            {
                "start": segment.start,
                "end": segment.end,
                "speaker": speaker,
                "text": segment.text,
            }
        )

    return result


def get_dominant_speaker(diarization, start, end):
    speakers = {}
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        if turn.start < end and turn.end > start:
            overlap = min(end, turn.end) - max(start, turn.start)
            speakers[speaker] = speakers.get(speaker, 0) + overlap
    return max(speakers, key=speakers.get) if speakers else "Unknown"


def format_time(seconds):
    minutes, seconds = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def save_result(result, output_file):
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# Transcription and Diarization Results\n\n")
        f.write("| Start Time | End Time | Speaker | Text |\n")
        f.write("|------------|----------|---------|------|\n")
        for segment in result:
            start = format_time(segment["start"])
            end = format_time(segment["end"])
            f.write(f"| {start} | {end} | {segment['speaker']} | {segment['text']} |\n")

        f.write("\n## Summary\n\n")
        speaker_times = {}
        for segment in result:
            speaker = segment["speaker"]
            duration = segment["end"] - segment["start"]
            speaker_times[speaker] = speaker_times.get(speaker, 0) + duration

        for speaker, time in speaker_times.items():
            f.write(f"- {speaker}: {time:.2f} seconds\n")


def main():
    parser = argparse.ArgumentParser(
        description="Transcribe and diarize an audio/video file"
    )
    parser.add_argument("input_file", help="Path to the input audio/video file")
    parser.add_argument("output_file", help="Path to save the result (Markdown)")
    parser.add_argument(
        "--auth_token",
        default=os.environ.get("HUGGINGFACE_TOKEN"),
        help="Hugging Face authentication token (default: HUGGINGFACE_TOKEN environment variable)",
    )
    parser.add_argument("--model_size", default="large-v2", help="Whisper model size")
    parser.add_argument(
        "--compute_type", default="float32", help="Compute type for Whisper model"
    )
    args = parser.parse_args()

    if not args.auth_token:
        print(
            "Error: Hugging Face authentication token is required. "
            "Set the HUGGINGFACE_TOKEN environment variable or use the --auth_token argument.",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        print(f"Processing {args.input_file}...")
        if torch.cuda.is_available():
            print("Using device: CUDA (NVIDIA GPU)")
        elif torch.backends.mps.is_available():
            print(
                "Using device: MPS (Apple Silicon GPU) for diarization, CPU for transcription"
            )
        else:
            print("Using device: CPU")

        audio_file = extract_audio(args.input_file)
        if not audio_file:
            print("Failed to extract audio. Exiting.")
            sys.exit(1)

        result = transcribe_and_diarize(
            audio_file, args.auth_token, args.model_size, args.compute_type
        )

        save_result(result, args.output_file)
        print(f"Result saved to {args.output_file}")

        # Print a summary to console
        print("\nSpeaker Summary:")
        speaker_times = {}
        for segment in result:
            speaker = segment["speaker"]
            duration = segment["end"] - segment["start"]
            speaker_times[speaker] = speaker_times.get(speaker, 0) + duration

        for speaker, time in speaker_times.items():
            print(f"{speaker}: {time:.2f} seconds")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
    finally:
        # Clean up temporary audio file
        if "audio_file" in locals() and os.path.exists(audio_file):
            os.remove(audio_file)
            print(f"Temporary audio file removed: {audio_file}")


if __name__ == "__main__":
    main()
