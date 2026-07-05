"""
CineLocalAI — Main Entry Point
================================
Run the full dubbing pipeline from the command line:

  python main.py --input path/to/video.mp4 --config config/settings.yaml

Or with quick overrides:

  python main.py --input movie.mp4 --src en --tgt hi --whisper small
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Optional

# Ensure UTF-8 output on Windows to prevent UnicodeEncodeError
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import yaml

# Ensure ffmpeg is on PATH and DLL load directories for whisper, torchcodec, and composer
import shutil
winget_dir = Path(os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages"))
ffmpeg_bin_dir = None

# 1. Search for shared FFmpeg build (needed for torchcodec DLL loading)
for pkg in winget_dir.glob("Gyan.FFmpeg.Shared_*"):
    bin_dir = pkg / "ffmpeg-8.1.2-full_build-shared" / "bin"
    if not bin_dir.exists():
        for sub in pkg.glob("**/bin"):
            if (sub / "avcodec-62.dll").exists() or (sub / "ffmpeg.exe").exists():
                bin_dir = sub
                break
    if bin_dir.exists() and (bin_dir / "ffmpeg.exe").exists():
        ffmpeg_bin_dir = bin_dir
        # Add DLL directory for Python DLL resolution on Windows (Python 3.8+)
        if hasattr(os, "add_dll_directory"):
            try:
                os.add_dll_directory(str(bin_dir))
            except Exception:
                pass
        break

# 2. Fall back to standard FFmpeg build if shared build was not found
if not ffmpeg_bin_dir:
    for pkg in winget_dir.glob("Gyan.FFmpeg_*"):
        bin_dir = pkg / "ffmpeg-8.1.2-full_build" / "bin"
        if not bin_dir.exists():
            for sub in pkg.glob("**/bin"):
                if (sub / "ffmpeg.exe").exists():
                    bin_dir = sub
                    break
        if bin_dir.exists() and (bin_dir / "ffmpeg.exe").exists():
            ffmpeg_bin_dir = bin_dir
            break

# Add resolved FFmpeg folder to PATH
if ffmpeg_bin_dir:
    os.environ["PATH"] = str(ffmpeg_bin_dir) + os.path.pathsep + os.environ.get("PATH", "")




def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None):
    """Configure structured logging for the pipeline."""
    fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        os.makedirs(os.path.dirname(log_file) or ".", exist_ok=True)
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))

    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format=fmt,
        handlers=handlers,
    )


def load_config(config_path: str) -> dict:
    """Load YAML config file."""
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="CineLocalAI — Fully local AI-powered video dubbing pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --input demo/sample.mp4
  python main.py --input demo/sample.mp4 --tgt fr --whisper small
  python main.py --input demo/sample.mp4 --config config/custom.yaml --gpu
        """,
    )

    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Path to the input video or audio file.",
    )
    parser.add_argument(
        "--config", "-c",
        default="config/settings.yaml",
        help="Path to YAML config file (default: config/settings.yaml).",
    )
    parser.add_argument(
        "--src",
        default=None,
        help="Override source language (e.g. 'en').",
    )
    parser.add_argument(
        "--tgt",
        default=None,
        help="Override target language (e.g. 'hi', 'fr', 'de').",
    )
    parser.add_argument(
        "--whisper",
        default=None,
        choices=["tiny", "base", "small", "medium", "large"],
        help="Override Whisper model size.",
    )
    parser.add_argument(
        "--speaker-wav",
        default=None,
        help="Path to reference speaker audio for TTS voice cloning.",
    )
    parser.add_argument(
        "--run-id",
        default=None,
        help="Custom run ID (used for checkpoints & output naming).",
    )
    parser.add_argument(
        "--gpu",
        action="store_true",
        help="Enable GPU acceleration for TTS.",
    )
    parser.add_argument(
        "--burn-subs",
        action="store_true",
        help="Hard-burn subtitles into the output video.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    parser.add_argument(
        "--log-file",
        default="outputs/logs/cinelocalai.log",
        help="Path to save log file.",
    )

    return parser.parse_args()


def main():
    from typing import Optional
    args = parse_args()
    setup_logging(args.log_level, args.log_file)

    logger = logging.getLogger("main")
    logger.info("╔══════════════════════════════════════╗")
    logger.info("║        CineLocalAI v1.0              ║")
    logger.info("║  Local AI Video Dubbing Pipeline     ║")
    logger.info("╚══════════════════════════════════════╝")

    # Load base config
    config_path = args.config
    if not os.path.isfile(config_path):
        logger.warning(f"Config not found at '{config_path}' — using defaults.")
        config = {}
    else:
        config = load_config(config_path)
        logger.info(f"Loaded config: {config_path}")

    # Apply CLI overrides
    if args.src:
        config["src_lang"] = args.src
    if args.tgt:
        config["tgt_lang"] = args.tgt
    if args.whisper:
        config["whisper_model"] = args.whisper
    if args.speaker_wav:
        config["speaker_wav"] = args.speaker_wav
    if args.run_id:
        config["run_id"] = args.run_id
    if args.gpu:
        config["use_gpu"] = True
    if args.burn_subs:
        config["burn_subtitles"] = True

    # Validate input
    input_path = str(Path(args.input).resolve())
    if not os.path.isfile(input_path):
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    # Run pipeline
    from orchestrator import CineLocalPipeline

    pipeline = CineLocalPipeline(config)
    result = pipeline.run(input_path)

    # Print summary
    logger.info("")
    logger.info("┌─────────────────────────────────────────┐")
    logger.info("│           Pipeline Summary               │")
    logger.info("├─────────────────────────────────────────┤")
    logger.info(f"│  Run ID      : {result['run_id']:<26}│")
    logger.info(f"│  Segments    : {result['segment_count']:<26}│")
    logger.info(f"│  Source Lang : {result['src_lang']:<26}│")
    logger.info(f"│  Target Lang : {result['tgt_lang']:<26}│")
    logger.info(f"│  Emotion     : {result['emotion_summary']['dominant_emotion']:<26}│")
    logger.info(f"│  Elapsed     : {result['elapsed_seconds']}s{' ' * (25 - len(str(result['elapsed_seconds'])))}│")
    logger.info("├─────────────────────────────────────────┤")
    logger.info(f"│  Output: {result['final_video']}")
    logger.info("└─────────────────────────────────────────┘")


if __name__ == "__main__":
    main()
