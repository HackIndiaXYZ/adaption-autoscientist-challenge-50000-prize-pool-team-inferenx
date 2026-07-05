"""
Transcript Agent
----------------
Transcribes audio/video files into timestamped text segments using OpenAI Whisper.
Supports local Whisper models via the `whisper` library (no API key required).
"""

import os
import logging
from pathlib import Path
from typing import Optional

import whisper

logger = logging.getLogger(__name__)


class TranscriptAgent:
    """
    Agent responsible for transcribing audio or video input into
    timestamped segments with speaker-language detection.
    """

    def __init__(self, model_size: str = "base", device: str = "cpu"):
        """
        Args:
            model_size: Whisper model size — tiny | base | small | medium | large
            device: 'cpu' or 'cuda'
        """
        self.model_size = model_size
        self.device = device
        self._model: Optional[whisper.Whisper] = None
        logger.info(f"[TranscriptAgent] Initialized | model={model_size} | device={device}")

    def _load_model(self) -> whisper.Whisper:
        """Lazy-load the Whisper model."""
        if self._model is None:
            logger.info(f"[TranscriptAgent] Loading Whisper model '{self.model_size}'...")
            self._model = whisper.load_model(self.model_size, device=self.device)
            logger.info("[TranscriptAgent] Model loaded successfully.")
        return self._model

    def transcribe(self, audio_path: str, language: Optional[str] = None) -> dict:
        """
        Transcribe an audio/video file.

        Args:
            audio_path: Path to the audio/video file.
            language:   Optional ISO language code (e.g. 'en', 'hi', 'fr').
                        If None, Whisper auto-detects.

        Returns:
            A dict with keys:
                - 'text'     : Full transcript string
                - 'segments' : List of dicts with 'start', 'end', 'text'
                - 'language' : Detected or specified language code
        """
        audio_path = str(Path(audio_path).resolve())
        if not os.path.isfile(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        model = self._load_model()
        logger.info(f"[TranscriptAgent] Transcribing: {audio_path}")

        options = {}
        if language:
            options["language"] = language

        result = model.transcribe(audio_path, **options, verbose=False)

        transcript = {
            "text": result.get("text", "").strip(),
            "segments": [
                {
                    "start": seg["start"],
                    "end":   seg["end"],
                    "text":  seg["text"].strip(),
                }
                for seg in result.get("segments", [])
            ],
            "language": result.get("language", "unknown"),
        }

        logger.info(
            f"[TranscriptAgent] Done | lang={transcript['language']} | "
            f"segments={len(transcript['segments'])}"
        )
        return transcript

    def save_transcript(self, transcript: dict, output_path: str) -> str:
        """
        Save transcript to a JSON file.

        Args:
            transcript:  Output from `transcribe()`.
            output_path: Destination .json file path.

        Returns:
            Absolute path of the saved file.
        """
        import json

        output_path = str(Path(output_path).resolve())
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(transcript, f, indent=2, ensure_ascii=False)

        logger.info(f"[TranscriptAgent] Transcript saved → {output_path}")
        return output_path
