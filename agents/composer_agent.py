"""
Composer Agent
--------------
Assembles the final dubbed video by combining:
  - Original video (with original audio muted or reduced)
  - Per-segment TTS audio files, time-aligned to original timestamps
  - Optional subtitle overlay (SRT/ASS format)

Uses FFmpeg (via subprocess) and pydub for audio mixing.
"""

import json
import logging
import os
import subprocess
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


class ComposerAgent:
    """
    Final-stage agent that merges dubbed TTS audio segments with
    the source video to produce a complete, time-aligned dubbed video.
    """

    def __init__(
        self,
        output_dir: str = "outputs/final",
        ffmpeg_path: str = "ffmpeg",
        original_audio_volume: float = 0.08,
    ):
        """
        Args:
            output_dir:             Directory for final output files.
            ffmpeg_path:            Path to FFmpeg binary (must be on PATH or absolute).
            original_audio_volume:  Volume multiplier for original audio bleed-through (0 = mute).
        """
        self.output_dir = output_dir
        self.ffmpeg = ffmpeg_path
        self.original_audio_volume = original_audio_volume
        os.makedirs(self.output_dir, exist_ok=True)
        logger.info(f"[ComposerAgent] Initialized | output_dir={output_dir}")

    # ------------------------------------------------------------------ #
    #  Audio Assembly                                                      #
    # ------------------------------------------------------------------ #

    def build_audio_track(
        self,
        segments: List[dict],
        video_duration: float,
        merged_audio_path: str,
    ) -> str:
        """
        Build a single merged WAV audio track from all TTS segment files,
        placed at their original timestamps.

        Args:
            segments:           Segments with 'start', 'end', 'audio_path'.
            video_duration:     Total duration of the source video in seconds.
            merged_audio_path:  Output path for the merged .wav file.

        Returns:
            Path to the merged audio file.
        """
        from pydub import AudioSegment

        logger.info("[ComposerAgent] Assembling merged audio track...")
        silence = AudioSegment.silent(duration=int(video_duration * 1000))

        for seg in segments:
            audio_path = seg.get("audio_path", "")
            if not audio_path or not os.path.isfile(audio_path):
                continue

            start_ms = int(seg.get("start", 0) * 1000)
            try:
                clip = AudioSegment.from_wav(audio_path)
                window_ms = int((seg.get("end", 0) - seg.get("start", 0)) * 1000)
                # If audio is longer than segment window, speed it up to fit
                if len(clip) > window_ms:
                    speed_ratio = len(clip) / window_ms
                    # Cap speedup to 1.5x to preserve intelligibility
                    if speed_ratio > 1.5:
                        speed_ratio = 1.5
                    try:
                        from pydub.effects import speedup
                        clip = speedup(clip, playback_speed=speed_ratio)
                    except Exception as e:
                        logger.warning(f"[ComposerAgent] speedup failed: {e}. Truncating instead.")
                    # Ensure it fits exactly (truncate if speedup rounding was slightly off)
                    if len(clip) > window_ms:
                        clip = clip[:window_ms]
                silence = silence.overlay(clip, position=start_ms)
            except Exception as e:
                logger.warning(f"[ComposerAgent] Could not load {audio_path}: {e}")

        os.makedirs(os.path.dirname(merged_audio_path) or ".", exist_ok=True)
        silence.export(merged_audio_path, format="wav")
        logger.info(f"[ComposerAgent] Audio track saved → {merged_audio_path}")
        return merged_audio_path

    # ------------------------------------------------------------------ #
    #  Subtitle Generation                                                 #
    # ------------------------------------------------------------------ #

    def generate_srt(self, segments: List[dict], srt_path: str) -> str:
        """
        Generate an SRT subtitle file from transcript segments.

        Args:
            segments: Segment dicts with 'start', 'end', 'translated_text'.
            srt_path: Output .srt file path.

        Returns:
            Path to the generated SRT file.
        """

        def _fmt_time(seconds: float) -> str:
            h = int(seconds // 3600)
            m = int((seconds % 3600) // 60)
            s = int(seconds % 60)
            ms = int((seconds - int(seconds)) * 1000)
            return f"{h:02}:{m:02}:{s:02},{ms:03}"

        os.makedirs(os.path.dirname(srt_path) or ".", exist_ok=True)
        with open(srt_path, "w", encoding="utf-8") as f:
            for i, seg in enumerate(segments, start=1):
                start = _fmt_time(seg.get("start", 0))
                end = _fmt_time(seg.get("end", 0))
                text = seg.get("translated_text") or seg.get("text", "")
                f.write(f"{i}\n{start} --> {end}\n{text}\n\n")

        logger.info(f"[ComposerAgent] SRT saved → {srt_path}")
        return srt_path

    # ------------------------------------------------------------------ #
    #  Final Video Composition                                             #
    # ------------------------------------------------------------------ #

    def compose(
        self,
        source_video: str,
        merged_audio: str,
        output_filename: str = "dubbed_output.mp4",
        srt_path: Optional[str] = None,
        burn_subtitles: bool = False,
    ) -> str:
        """
        Merge dubbed audio with the source video using FFmpeg.

        Args:
            source_video:    Path to the original video file.
            merged_audio:    Path to the merged dubbed .wav audio track.
            output_filename: Name of the final output video file.
            srt_path:        Optional .srt file for subtitle overlay.
            burn_subtitles:  If True, hard-burn subtitles into video.

        Returns:
            Absolute path to the composed video file.
        """
        output_path = str(Path(self.output_dir) / output_filename)
        logger.info(f"[ComposerAgent] Composing final video → {output_path}")

        # Map video stream from input 0 (source video) and audio from input 1 (dubbed audio)
        cmd = [
            self.ffmpeg, "-y",
            "-i", source_video,
            "-i", merged_audio,
            "-map", "0:v",
            "-map", "1:a",
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
        ]

        if burn_subtitles and srt_path and os.path.isfile(srt_path):
            # Fix: Convert Windows backslashes → forward slashes for FFmpeg's subtitles filter.
            # FFmpeg's libass filter does not accept Windows-style paths.
            srt_ffmpeg = srt_path.replace("\\", "/")
            # If burning subtitles, we cannot use stream copy (-c:v copy).
            # Replace 'copy' with 'libx264' encoder.
            if "-c:v" in cmd:
                idx_cv = cmd.index("-c:v")
                cmd[idx_cv + 1] = "libx264"
            cmd += ["-vf", f"subtitles='{srt_ffmpeg}'"]

        cmd.append(output_path)

        logger.debug(f"[ComposerAgent] FFmpeg cmd: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            stderr_tail = result.stderr[-800:]
            # Provide a specific hint for the common 'no audio stream' failure
            if "no such stream" in stderr_tail.lower() or "audio" in stderr_tail.lower():
                logger.error(
                    "[ComposerAgent] FFmpeg could not find an audio stream in the source video. "
                    "Ensure the input file has an audio track."
                )
            logger.error(f"[ComposerAgent] FFmpeg error:\n{stderr_tail}")
            raise RuntimeError(
                f"FFmpeg composition failed (exit {result.returncode}). "
                f"See logs above for details. Last stderr:\n{stderr_tail}"
            )

        logger.info(f"[ComposerAgent] ✓ Output video: {output_path}")
        return output_path

    # ------------------------------------------------------------------ #
    #  Metadata Export                                                     #
    # ------------------------------------------------------------------ #

    def export_metadata(self, pipeline_result: dict, metadata_path: str) -> str:
        """
        Export a JSON metadata file summarizing the full pipeline run.

        Args:
            pipeline_result: Dict containing pipeline output data.
            metadata_path:   Output JSON path.

        Returns:
            Path to the saved metadata file.
        """
        os.makedirs(os.path.dirname(metadata_path) or ".", exist_ok=True)
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(pipeline_result, f, indent=2, ensure_ascii=False)
        logger.info(f"[ComposerAgent] Metadata saved → {metadata_path}")
        return metadata_path
