# Transcription and Diarization

A Python script to transcribe and diarize audio/video files using Faster Whisper and Pyannote.audio.

## Installation

1. Navigate to the `transcription` directory
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
3. Create a HuggingFace access token at [`hf.co/settings/tokens`](https://hf.co/settings/tokens)

4. Set up environment variables:

   - Set `HUGGINGFACE_TOKEN` with the access token you created

5. Accept user conditions for Pyannote.audio models:

   - Accept [`pyannote/segmentation-3.0`](https://hf.co/pyannote/segmentation-3.0) user conditions
   - Accept [`pyannote/speaker-diarization-3.1`](https://hf.co/pyannote/speaker-diarization-3.1) user conditions

6. Install FFmpeg on your system (required for audio extraction)

## Usage

```
python transcription.py [options] input_file output_file
```

### Options

- `--auth_token TOKEN`: Hugging Face authentication token (default: HUGGINGFACE_TOKEN environment variable)
- `--model_size SIZE`: Whisper model size (default: large-v2)
- `--compute_type TYPE`: Compute type for Whisper model (default: float32)

### Examples

```
python transcription.py input_video.mp4 output_transcript.md
python transcription.py --model_size medium input_audio.wav output_transcript.md
python transcription.py --compute_type float16 input_video.mp4 output_transcript.md
```

## Features

- Audio extraction from video files using FFmpeg
- Transcription using Faster Whisper model
- Speaker diarization using Pyannote.audio
- Support for GPU acceleration (CUDA and MPS)
- Progress indicator during transcription
- Markdown output with timestamped transcripts and speaker labels

## Output

The script generates a markdown file with:

1. Timestamped transcripts with speaker labels
2. Summary of speaking time for each speaker

## Notes

- Ensure FFmpeg is installed on your system
- GPU acceleration is used for diarization if available
- Transcription always uses CPU for compatibility
- Temporary audio files are automatically cleaned up after processing

## Citations

If you use this script, which incorporates `pyannote.audio`, please use the following citations:

```bibtex
@inproceedings{Plaquet23,
  author={Alexis Plaquet and Hervé Bredin},
  title={{Powerset multi-class cross entropy loss for neural speaker diarization}},
  year=2023,
  booktitle={Proc. INTERSPEECH 2023},
}
```

```bibtex
@inproceedings{Bredin23,
  author={Hervé Bredin},
  title={{pyannote.audio 2.1 speaker diarization pipeline: principle, benchmark, and recipe}},
  year=2023,
  booktitle={Proc. INTERSPEECH 2023},
}
```
