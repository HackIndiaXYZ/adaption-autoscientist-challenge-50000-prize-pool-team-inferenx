"""
TTS Agent (Text-to-Speech)
--------------------------
Converts translated text segments into speech audio files.
Uses the Coqui TTS library (local, offline).

Two operating modes:
  1. XTTS v2  — voice cloning; requires speaker_wav (6-30s reference .wav).
  2. Fallback — single-speaker, language-specific; zero-config, no reference audio needed.

MVP default: fallback mode (speaker_wav = null in config).
"""

import logging
import os
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

# Emotion → prosody hints.
# NOTE: These are reserved for future post-processing (e.g. audio stretching via pydub).
# They are NOT passed to the TTS API — neither XTTS v2 nor the fallback models
# accept speed/pitch via tts_to_file().
EMOTION_PROSODY = {
    "joyful":      {"speed": 1.1,  "pitch": 2},
    "melancholic": {"speed": 0.88, "pitch": -2},
    "intense":     {"speed": 1.15, "pitch": 1},
    "tense":       {"speed": 0.95, "pitch": -1},
    "grim":        {"speed": 0.90, "pitch": -3},
    "surprising":  {"speed": 1.05, "pitch": 3},
    "neutral":     {"speed": 1.0,  "pitch": 0},
}

# XTTS v2 — used only when speaker_wav is provided
DEFAULT_TTS_MODEL = "tts_models/multilingual/multi-dataset/xtts_v2"

# Fallback single-speaker models (no reference audio required).
# Downloaded automatically on first use (~50–300 MB each).
FALLBACK_MODELS: dict = {
    "en": "tts_models/en/ljspeech/tacotron2-DDC",
    "fr": "tts_models/fr/css10/vits",
    "de": "tts_models/de/thorsten/tacotron2-DDC",
    "es": "tts_models/es/css10/vits",
    "it": "tts_models/it/mai_female/vits",
    "zh": "tts_models/zh-CN/baker/tacotron2-DDC-GST",
}


class TTSAgent:
    """
    Generates speech from translated transcript segments using Coqui TTS.

    Mode A — XTTS v2 (voice cloning):
        Set speaker_wav to a 6–30s .wav reference clip.
        Produces high-quality cloned voice output.
        Requires ~1.8 GB model download.

    Mode B — Fallback (single-speaker, zero-config):
        Leave speaker_wav as None (default).
        Auto-selects a language-specific model.
        No reference audio required.
        Suitable for MVP / first-run testing.
    """

    def __init__(
        self,
        model_name: str = DEFAULT_TTS_MODEL,
        output_dir: str = "outputs/tts",
        speaker_wav: Optional[str] = None,
        language: str = "hi",
        use_gpu: bool = False,
    ):
        """
        Args:
            model_name:  Coqui TTS model ID. Only used when speaker_wav is set (XTTS v2 mode).
            output_dir:  Directory to write generated .wav files.
            speaker_wav: Path to 6-30s reference audio for XTTS v2 voice cloning.
                         If None (default), a single-speaker fallback model is chosen
                         automatically by language — no reference audio required.
                         RECOMMENDED for CPU-only environments.
            language:    Target synthesis language (ISO 639-1, e.g. 'hi', 'en').
            use_gpu:     GPU acceleration flag. Must be False on CPU-only systems.
                         XTTS v2 on CPU takes ~5-15 min per segment — use fallback
                         mode (speaker_wav=None) for practical CPU performance.
        """
        self.output_dir = output_dir
        self.speaker_wav = speaker_wav
        self.language = language
        self.use_gpu = use_gpu
        self._tts = None

        # Select mode
        self._using_fallback = (speaker_wav is None)
        
        # Supported languages in XTTS v2
        xtts_supported_langs = {
            "en", "es", "fr", "de", "it", "pt", "pl", "tr", "ru", 
            "nl", "cs", "ar", "zh", "hu", "ko", "ja", "hi"
        }
        
        # If language is not supported by XTTS v2, force fallback mode
        if not self._using_fallback and language.lower() not in xtts_supported_langs:
            logger.warning(
                f"[TTSAgent] Language '{language}' is not supported by XTTS v2 voice cloning. "
                "Forcing fallback mode to single-speaker model."
            )
            self._using_fallback = True

        if self._using_fallback:
            if language.lower() == "hi":
                self.model_name = DEFAULT_TTS_MODEL
                logger.warning(
                    f"[TTSAgent] speaker_wav not set for language='{language}' — FALLBACK mode active. "
                    f"Will attempt to use default model '{self.model_name}' but a voice sample is required before synthesis."
                )
            else:
                self.model_name = self._resolve_fallback_model(language)
                logger.warning(
                    f"[TTSAgent] Fallback mode active. Using single-speaker model: '{self.model_name}'."
                )
        else:
            self.model_name = model_name
            logger.info(f"[TTSAgent] XTTS v2 mode | speaker_wav={speaker_wav}")

        # Estimate speaker gender from reference audio
        self.speaker_gender = "unknown"
        if self.speaker_wav and os.path.exists(self.speaker_wav):
            self.speaker_gender = self._estimate_gender(self.speaker_wav)
            logger.info(f"[TTSAgent] Estimated speaker gender from '{self.speaker_wav}': {self.speaker_gender}")

        os.makedirs(self.output_dir, exist_ok=True)
        logger.info(
            f"[TTSAgent] Initialized | model={self.model_name} | "
            f"lang={language} | gpu={use_gpu} | "
            f"mode={'fallback' if self._using_fallback else 'xtts_v2'}"
        )

    @staticmethod
    def _resolve_fallback_model(language: str) -> str:
        """Select the best no-reference-audio model for the target language."""
        model = FALLBACK_MODELS.get(language.lower())
        if model is None:
            logger.warning(
                f"[TTSAgent] No fallback model defined for language='{language}'. "
                "Defaulting to English tacotron2-DDC. "
                "Output audio will be in English regardless of translated text language."
            )
            model = FALLBACK_MODELS["en"]
        return model

    def _estimate_gender(self, wav_path: str) -> str:
        """Estimate the gender of the speaker in the reference WAV file using fundamental frequency (F0)."""
        import wave
        import numpy as np
        try:
            with wave.open(wav_path, 'rb') as w:
                params = w.getparams()
                num_channels = params.nchannels
                sample_width = params.sampwidth
                sample_rate = params.framerate
                num_frames = params.nframes
                
                raw_data = w.readframes(num_frames)
                
                if sample_width == 2:
                    dtype = np.int16
                elif sample_width == 4:
                    dtype = np.int32
                else:
                    dtype = np.int8
                    
                data = np.frombuffer(raw_data, dtype=dtype)
                if num_channels > 1:
                    data = data.reshape(-1, num_channels).mean(axis=1)
                    
                # Analyze in 1-second chunks and take median F0
                chunk_size = sample_rate
                f0s = []
                
                min_lag = int(sample_rate / 350)
                max_lag = int(sample_rate / 75)
                
                for i in range(0, len(data) - chunk_size, chunk_size):
                    clip = data[i:i+chunk_size]
                    if np.max(np.abs(clip)) < 100:  # Skip silent clips
                        continue
                        
                    corr = np.correlate(clip, clip, mode='full')
                    corr = corr[len(corr)//2:]
                    
                    if min_lag < len(corr) and max_lag < len(corr):
                        lag = np.argmax(corr[min_lag:max_lag]) + min_lag
                        f0 = sample_rate / lag
                        f0s.append(f0)
                        
                if f0s:
                    median_f0 = np.median(f0s)
                    if 75 <= median_f0 <= 165:
                        return "male"
                    else:
                        return "female"
        except Exception as e:
            logger.warning(f"[TTSAgent] Could not estimate speaker gender from WAV: {e}")
        return "unknown"

    def apply_emotion_prosody(self, audio_path: str, emotion: str):
        """Apply emotion-based speed and pitch modifications to the generated speech clip."""
        if not os.path.exists(audio_path):
            return
            
        prosody = EMOTION_PROSODY.get(emotion or "neutral", EMOTION_PROSODY["neutral"])
        speed = prosody.get("speed", 1.0)
        pitch = prosody.get("pitch", 0)
        
        if speed == 1.0 and pitch == 0:
            return
            
        try:
            from pydub import AudioSegment
            from pydub.effects import speedup
            
            sound = AudioSegment.from_wav(audio_path)
            
            # Pitch shifting
            pitch_factor = 1.059463 ** pitch
            if pitch != 0:
                new_sample_rate = int(sound.frame_rate * pitch_factor)
                sound = sound._spawn(sound.raw_data, overrides={'frame_rate': new_sample_rate}).set_frame_rate(sound.frame_rate)
                
            # Speed adjustment
            effective_speed = speed * pitch_factor
            if effective_speed > 1.0:
                sound = speedup(sound, playback_speed=effective_speed)
                
            sound.export(audio_path, format="wav")
            logger.info(
                f"[TTSAgent] Applied emotion prosody for '{emotion}': speed={speed}, pitch={pitch} (effective_speed={effective_speed:.2f})"
            )
        except Exception as e:
            logger.warning(f"[TTSAgent] Failed to apply emotion prosody: {e}")

    def _load_tts(self):
        """Lazy-load the selected Coqui TTS model."""
        if self._tts is None:
            if self.language.lower() == "hi" and self.speaker_wav is None:
                raise ValueError(
                    "Hindi ('hi') does not have a single-speaker fallback model in Coqui TTS. "
                    "A speaker reference audio file (.wav) is required for Hindi speech synthesis via XTTS v2. "
                    "Please set 'speaker_wav' in config/settings.yaml or pass '--speaker-wav'."
                )
            # Auto-agree to Coqui Terms of Service for non-interactive downloads
            os.environ["COQUI_TOS_AGREED"] = "1"
            from TTS.api import TTS
            logger.info(f"[TTSAgent] Loading model '{self.model_name}' (first-time download may take a while)...")
            self._tts = TTS(model_name=self.model_name, gpu=self.use_gpu)
            logger.info("[TTSAgent] Model ready.")
        return self._tts

    def synthesize_segment(
        self,
        text: str,
        segment_id: int,
        emotion: Optional[str] = "neutral",
    ) -> str:
        """
        Synthesize speech for a single text segment.

        Args:
            text:       Text to convert to speech.
            segment_id: Integer ID used to name the output file.
            emotion:    Cinematic emotion label (logged only; prosody reserved for future).

        Returns:
            Absolute path to the generated .wav file, or "" if text is empty.
        """
        if not text.strip():
            logger.warning(f"[TTSAgent] Segment {segment_id} is empty — skipping.")
            return ""

        output_file = str(Path(self.output_dir) / f"segment_{segment_id:04d}.wav")

        prosody = EMOTION_PROSODY.get(emotion or "neutral", EMOTION_PROSODY["neutral"])
        logger.debug(
            f"[TTSAgent] Synthesizing seg={segment_id} | emotion={emotion} | "
            f"speed_hint={prosody['speed']} | pitch_hint={prosody['pitch']} "
            f"(hints for post-processing only)"
        )

        if self._using_fallback:
            gtts_success = False
            # Use gTTS for languages that do not have a native Coqui fallback model (like Telugu)
            if self.language.lower() not in FALLBACK_MODELS:
                try:
                    from gtts import gTTS
                    import subprocess
                    
                    logger.info(f"[TTSAgent] Synthesizing '{self.language}' using gTTS...")
                    temp_mp3 = output_file.replace(".wav", ".mp3")
                    tts_gtts = gTTS(text=text, lang=self.language.lower())
                    tts_gtts.save(temp_mp3)
                    
                    # Convert MP3 to WAV using FFmpeg
                    ffmpeg_cmd = "ffmpeg"
                    import shutil
                    if not shutil.which(ffmpeg_cmd):
                        winget_dir = Path(os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages"))
                        for pkg in winget_dir.glob("Gyan.FFmpeg*"):
                            for sub in pkg.glob("**/ffmpeg.exe"):
                                if sub.exists():
                                    ffmpeg_cmd = str(sub)
                                    break
                            if ffmpeg_cmd != "ffmpeg":
                                break
                                
                    subprocess.run(
                        [ffmpeg_cmd, "-y", "-i", temp_mp3, output_file],
                        capture_output=True,
                        check=True,
                    )
                    
                    if os.path.exists(temp_mp3):
                        os.remove(temp_mp3)
                    gtts_success = True
                except Exception as e:
                    logger.warning(f"[TTSAgent] gTTS synthesis failed ({e}). Falling back to Coqui model.")

            if not gtts_success:
                # Mode B: single-speaker model — no extra kwargs
                tts = self._load_tts()
                tts.tts_to_file(text=text, file_path=output_file)
        else:
            # Mode A: XTTS v2 — speaker_wav required; speed/pitch NOT accepted by this API
            tts = self._load_tts()
            tts.tts_to_file(
                text=text,
                file_path=output_file,
                language=self.language,
                speaker_wav=self.speaker_wav,
            )

        # Apply gender-preservation pitch shifting to fallback outputs if a male speaker is detected
        if self._using_fallback and self.language.lower() != "de" and self.speaker_gender == "male" and os.path.exists(output_file):
            try:
                from pydub import AudioSegment
                from pydub.effects import speedup
                sound = AudioSegment.from_wav(output_file)
                # Shift pitch down by 4 semitones (factor of ~0.79)
                pitch_factor = 1.059463 ** -4
                new_sample_rate = int(sound.frame_rate * pitch_factor)
                sound_deeper = sound._spawn(sound.raw_data, overrides={'frame_rate': new_sample_rate}).set_frame_rate(sound.frame_rate)
                # Restore speed using speedup
                restored_sound = speedup(sound_deeper, playback_speed=1.26)
                restored_sound.export(output_file, format="wav")
                logger.info(f"[TTSAgent] Preserved male voice characteristics for fallback audio via pitch shifting.")
            except Exception as e:
                logger.warning(f"[TTSAgent] Failed to apply male voice shift: {e}")

        # Apply emotion prosody post-processing
        if emotion and emotion != "neutral":
            self.apply_emotion_prosody(output_file, emotion)

        logger.debug(f"[TTSAgent] Saved → {output_file}")
        return output_file

    def synthesize_all(self, segments: List[dict]) -> List[dict]:
        """
        Synthesize all translated segments in order.

        Args:
            segments: List of segment dicts with 'translated_text' and optional 'emotion'.

        Returns:
            Segments enriched with 'audio_path' key pointing to the .wav output.
        """
        logger.info(f"[TTSAgent] Synthesizing {len(segments)} segments...")
        result = []

        for i, seg in enumerate(segments):
            text = seg.get("translated_text") or seg.get("text", "")
            emotion_data = seg.get("emotion", {})
            emotion_label = (
                emotion_data.get("cinematic_label")
                if isinstance(emotion_data, dict)
                else "neutral"
            )
            audio_path = self.synthesize_segment(text, segment_id=i, emotion=emotion_label)
            result.append({**seg, "audio_path": audio_path})

        logger.info(f"[TTSAgent] All segments synthesized. Output dir: {self.output_dir}")
        return result

    def list_available_models(self) -> List[str]:
        """List all Coqui TTS models available for download."""
        from TTS.api import TTS
        return TTS().list_models()
