"""
Orchestration Pipeline
----------------------
Coordinates all CineLocalAI agents in a sequential pipeline:

  1. TranscriptAgent  → transcribe audio/video to text
  2. EmotionTagger    → tag each segment with emotion
  3. TranslationAgent → translate segments to target language
  4. TTSAgent         → synthesize dubbed audio per segment
  5. ComposerAgent    → assemble final dubbed video

Supports checkpoint saving so long pipelines can be resumed.
"""

import json
import logging
import os
import subprocess
import time
from pathlib import Path
from typing import Optional

from agents import (
    ComposerAgent,
    EmotionTagger,
    TranscriptAgent,
    TranslationAgent,
    TTSAgent,
)
from orchestrator.model_router import ModelRouter

logger = logging.getLogger(__name__)


class CineLocalPipeline:
    """
    End-to-end dubbing pipeline for CineLocalAI.
    Each stage can be individually skipped if checkpoint data exists.
    """

    def __init__(self, config: dict):
        """
        Args:
            config: Configuration dictionary (mirrors config/settings.yaml keys).
        """
        self.config = config
        self.run_id = config.get("run_id", f"run_{int(time.time())}")
        self.checkpoint_dir = Path(config.get("checkpoint_dir", "data/checkpoints")) / self.run_id
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        # ── Instantiate all agents ──────────────────────────────────────
        self.transcript_agent = TranscriptAgent(
            model_size=config.get("whisper_model", "base"),
            device=config.get("whisper_device", "cpu"),
        )
        self.emotion_tagger = EmotionTagger(
            model_name=config.get("emotion_model", None),
            device=config.get("emotion_device", -1),
        )
        self.translation_agent = ModelRouter(config)
        self.tts_agent = TTSAgent(
            model_name=config.get("tts_model", "tts_models/multilingual/multi-dataset/xtts_v2"),
            output_dir=config.get("tts_output_dir", "outputs/tts"),
            speaker_wav=config.get("speaker_wav", None),
            language=config.get("tgt_lang", "hi"),
            use_gpu=config.get("use_gpu", False),
        )
        self.composer_agent = ComposerAgent(
            output_dir=config.get("final_output_dir", "outputs/final"),
            ffmpeg_path=config.get("ffmpeg_path", "ffmpeg"),
            original_audio_volume=config.get("original_audio_volume", 0.08),
        )

    # ------------------------------------------------------------------ #
    #  Checkpoint Helpers                                                  #
    # ------------------------------------------------------------------ #

    def _ckpt_path(self, stage: str) -> Path:
        return self.checkpoint_dir / f"{stage}.json"

    def _save_checkpoint(self, stage: str, data: object):
        path = self._ckpt_path(stage)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"[Pipeline] Checkpoint saved: {path}")

    def _load_checkpoint(self, stage: str) -> Optional[object]:
        path = self._ckpt_path(stage)
        if path.exists():
            logger.info(f"[Pipeline] Resuming from checkpoint: {path}")
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    # ------------------------------------------------------------------ #
    #  Pipeline Execution                                                  #
    # ------------------------------------------------------------------ #

    def run(self, source_video: str) -> dict:
        """
        Execute the full dubbing pipeline.

        Args:
            source_video: Path to the input video/audio file.

        Returns:
            dict summarizing the pipeline output paths and metadata.
        """
        source_video = str(Path(source_video).resolve())

        # Fix #5: Validate FFmpeg is available before doing any model work.
        ffmpeg_bin = self.config.get("ffmpeg_path", "ffmpeg")
        try:
            subprocess.run(
                [ffmpeg_bin, "-version"],
                capture_output=True,
                check=True,
            )
        except (FileNotFoundError, subprocess.CalledProcessError) as exc:
            raise RuntimeError(
                f"[Pipeline] FFmpeg not found at '{ffmpeg_bin}'. "
                "Install FFmpeg and ensure it is on your PATH, or set "
                "'ffmpeg_path' in config/settings.yaml to its absolute path."
            ) from exc

        logger.info(f"[Pipeline] ═══ Starting CineLocalAI Pipeline ═══")
        logger.info(f"[Pipeline] Source  : {source_video}")
        logger.info(f"[Pipeline] Run ID  : {self.run_id}")
        logger.info(f"[Pipeline] Lang    : {self.config.get('src_lang')} → {self.config.get('tgt_lang')}")

        t_start = time.time()

        # ── Stage 1: Transcription ──────────────────────────────────────
        transcript = self._load_checkpoint("transcript")
        if transcript is None:
            logger.info("[Pipeline] Stage 1/5 → Transcription")
            transcript = self.transcript_agent.transcribe(
                source_video,
                language=self.config.get("src_lang"),
            )
            self.transcript_agent.save_transcript(
                transcript,
                output_path=f"data/transcripts/{self.run_id}_transcript.json",
            )
            self._save_checkpoint("transcript", transcript)
        else:
            logger.info("[Pipeline] Stage 1/5 → Transcription (cached)")

        segments = transcript["segments"]

        # Fix #4: Guard against empty transcript (silent video, wrong language, etc.)
        if not segments:
            raise RuntimeError(
                "[Pipeline] Transcription returned 0 segments. "
                "Check that the input file contains audible speech and that "
                "'src_lang' in config matches the spoken language."
            )

        # ── Stage 2: Emotion Tagging ────────────────────────────────────
        tagged = self._load_checkpoint("emotion_tagged")
        if tagged is None:
            logger.info("[Pipeline] Stage 2/5 → Emotion Tagging")
            tagged = self.emotion_tagger.tag_transcript(segments)
            self._save_checkpoint("emotion_tagged", tagged)
        else:
            logger.info("[Pipeline] Stage 2/5 → Emotion Tagging (cached)")

        emotion_summary = self.emotion_tagger.summarize_emotions(tagged)
        logger.info(f"[Pipeline] Dominant emotion: {emotion_summary['dominant_emotion']}")

        # ── Stage 3: Translation ────────────────────────────────────────
        translated = self._load_checkpoint("translated")
        if translated is None:
            logger.info("[Pipeline] Stage 3/5 → Translation")
            translated = self.translation_agent.translate_segments(tagged)
            self._save_checkpoint("translated", translated)
        else:
            logger.info("[Pipeline] Stage 3/5 → Translation (cached)")

        # ── Stage 4: TTS Synthesis ──────────────────────────────────────
        synthesized = self._load_checkpoint("synthesized")
        if synthesized is None:
            # Auto-extract speaker_wav if no reference was provided (supported for all languages)
            if not self.tts_agent.speaker_wav:
                auto_speaker_wav = self.checkpoint_dir / "extracted_speaker.wav"
                if not auto_speaker_wav.exists():
                    # Task 2 & 3: Find longest speech segment from transcript timestamps
                    candidates = []
                    for idx, seg in enumerate(segments):
                        start = seg.get("start", 0.0)
                        end = seg.get("end", 0.0)
                        text = seg.get("text", "").strip()
                        duration = end - start
                        if duration >= 2.0 and text:
                            candidates.append({
                                "index": idx,
                                "start": start,
                                "end": end,
                                "duration": duration,
                                "text": text
                            })
                            
                    logger.info(f"[SpeakerProfile] Candidate segments found: {len(candidates)}")
                    
                    selected_start = 0.0
                    selected_duration = 6.0
                    
                    if candidates:
                        # Find longest segment. For ties, select the earliest index (first encountered)
                        selected = max(candidates, key=lambda c: (c["duration"], -c["index"]))
                        selected_start = selected["start"]
                        selected_duration = selected["duration"]
                        
                        logger.info(
                            f"[SpeakerProfile] Selected segment: "
                            f"start={selected_start:.2f} end={selected['end']:.2f} duration={selected_duration:.2f}"
                        )
                    else:
                        logger.info("[SpeakerProfile] No valid segment >= 2.0s found. Falling back to default first 6s extraction.")
                        
                    logger.info(f"[Pipeline] No speaker_wav was provided. Auto-extracting speaker voice sample from source video...")
                    ffmpeg_bin = self.config.get("ffmpeg_path", "ffmpeg")
                    try:
                        subprocess.run(
                            [
                                ffmpeg_bin, "-y",
                                "-i", source_video,
                                "-ss", str(selected_start), "-t", str(selected_duration),
                                "-acodec", "pcm_s16le",
                                "-ar", "22050",
                                "-ac", "1",
                                str(auto_speaker_wav)
                            ],
                            capture_output=True,
                            check=True,
                        )
                        logger.info(f"[SpeakerProfile] Extracted speaker sample: path={auto_speaker_wav}")
                    except Exception as e:
                        logger.warning(f"[Pipeline] Failed to auto-extract speaker reference: {e}.")
                
                if auto_speaker_wav.exists():
                    self.tts_agent.speaker_wav = str(auto_speaker_wav)
                    supported_xtts_langs = {
                        "en", "es", "fr", "de", "it", "pt", "pl", "tr", "ru", 
                        "nl", "cs", "ar", "zh", "hu", "ko", "ja", "hi"
                    }
                    if self.config.get("tgt_lang") in supported_xtts_langs:
                        self.tts_agent._using_fallback = False
                        self.tts_agent.model_name = self.config.get("tts_model", "tts_models/multilingual/multi-dataset/xtts_v2")
                        logger.info("[Pipeline] TTSAgent updated to use XTTS v2 with auto-extracted reference audio.")
                    else:
                        logger.info("[Pipeline] TTSAgent keeping fallback mode but using auto-extracted reference audio for voice profiling.")
                    
                    if hasattr(self.tts_agent, "_estimate_gender"):
                        self.tts_agent.speaker_gender = self.tts_agent._estimate_gender(self.tts_agent.speaker_wav)

            logger.info("[Pipeline] Stage 4/5 → TTS Synthesis")
            synthesized = self.tts_agent.synthesize_all(translated)
            self._save_checkpoint("synthesized", synthesized)
        else:
            logger.info("[Pipeline] Stage 4/5 → TTS Synthesis (cached)")

        # ── Stage 5: Composition ────────────────────────────────────────
        logger.info("[Pipeline] Stage 5/5 → Video Composition")

        video_duration = segments[-1]["end"]  # Safe: empty-segments guard above ensures len >= 1
        merged_audio = str(self.checkpoint_dir / "merged_dubbed.wav")

        self.composer_agent.build_audio_track(synthesized, video_duration, merged_audio)

        srt_path = str(self.checkpoint_dir / "subtitles.srt")
        self.composer_agent.generate_srt(synthesized, srt_path)

        final_video = self.composer_agent.compose(
            source_video=source_video,
            merged_audio=merged_audio,
            output_filename=f"{self.run_id}_dubbed.mp4",
            srt_path=srt_path,
            burn_subtitles=self.config.get("burn_subtitles", False),
        )

        elapsed = round(time.time() - t_start, 2)

        result = {
            "run_id":          self.run_id,
            "source_video":    source_video,
            "final_video":     final_video,
            "srt_path":        srt_path,
            "emotion_summary": emotion_summary,
            "segment_count":   len(segments),
            "src_lang":        transcript.get("language"),
            "tgt_lang":        self.config.get("tgt_lang"),
            "elapsed_seconds": elapsed,
        }

        metadata_path = f"outputs/final/{self.run_id}_metadata.json"
        self.composer_agent.export_metadata(result, metadata_path)

        logger.info(f"[Pipeline] ═══ Pipeline complete in {elapsed}s ═══")
        logger.info(f"[Pipeline] Output: {final_video}")
        return result
