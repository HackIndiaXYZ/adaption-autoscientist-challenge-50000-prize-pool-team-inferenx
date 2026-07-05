"""
CineLocalAI Demo Script
------------------------
Quick demo that runs the pipeline on a sample video.
Place your test video at demo/sample.mp4 and run:

    python demo/run_demo.py
"""

from pathlib import Path
import logging
import os
import sys

# Ensure UTF-8 output on Windows to prevent UnicodeEncodeError
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure the project root is on sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Ensure ffmpeg is on PATH and DLL load directories for whisper, torchcodec, and composer
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


from orchestrator import CineLocalPipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

DEMO_CONFIG = {
    "run_id":                "demo_quick_test",
    "src_lang":              "en",
    "tgt_lang":              "hi",
    "whisper_model":         "base",
    "whisper_device":        "cpu",
    "emotion_model":         None,
    "emotion_device":        -1,
    "translation_device":    -1,
    "tts_model":             "tts_models/multilingual/multi-dataset/xtts_v2",
    "tts_output_dir":        "outputs/tts",
    "speaker_wav":           None,
    "use_gpu":               False,
    "final_output_dir":      "outputs/final",
    "ffmpeg_path":           "C:\\Users\\konne balraju\\AppData\\Local\\Microsoft\\WinGet\\Packages\\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\\ffmpeg-8.1.2-full_build\\bin\\ffmpeg.exe",
    "original_audio_volume": 0.08,
    "burn_subtitles":        False,
    "checkpoint_dir":        "data/checkpoints",
}

DEMO_VIDEO = os.path.join(os.path.dirname(__file__), "sample.mp4")

if __name__ == "__main__":
    if not os.path.isfile(DEMO_VIDEO):
        print(f"[Demo] Please place a video file at: {DEMO_VIDEO}")
        sys.exit(1)

    pipeline = CineLocalPipeline(DEMO_CONFIG)
    result = pipeline.run(DEMO_VIDEO)
    print(f"\n[Demo] ✓ Done! Output: {result['final_video']}")
