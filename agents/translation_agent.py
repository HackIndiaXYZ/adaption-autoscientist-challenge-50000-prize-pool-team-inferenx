"""
Translation Agent
-----------------
Translates transcript segments into a target language using
the facebook/nllb-200-distilled-600M model.
All inference is fully offline — no API keys required.
"""

import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)

# Supported language pairs mapping to NLLB-200 language codes
NLLB_LANG_MAP = {
    "en": "eng_Latn",
    "hi": "hin_Deva",
    "te": "tel_Telu",
    "fr": "fra_Latn",
    "de": "deu_Latn",
    "es": "spa_Latn",
    "it": "ita_Latn",
    "zh": "zho_Hans"
}

SUPPORTED_PAIRS = {
    ("en", "hi"),
    ("en", "te"),
    ("en", "fr"),
    ("en", "de"),
    ("en", "es"),
    ("en", "it"),
    ("en", "zh"),
    ("hi", "en"),
    ("fr", "en")
}


class TranslationAgent:
    """
    Translates text segments between supported language pairs
    using the local NLLB-200 model from HuggingFace.
    """

    def __init__(self, src_lang: str = "en", tgt_lang: str = "hi", device: int = -1):
        """
        Args:
            src_lang: ISO source language code (e.g. 'en').
            tgt_lang: ISO target language code (e.g. 'hi' or 'te').
            device:   -1 for CPU, 0+ for CUDA.
        """
        self.src_lang = src_lang.lower()
        self.tgt_lang = tgt_lang.lower()
        self.device = device
        self._tokenizer = None
        self._model = None
        self.model_id = "facebook/nllb-200-distilled-600M"
        
        # Verify supported pairs
        key: Tuple[str, str] = (self.src_lang, self.tgt_lang)
        if key not in SUPPORTED_PAIRS:
            raise ValueError(
                f"Language pair ({self.src_lang} → {self.tgt_lang}) not supported. "
                f"Supported: {list(SUPPORTED_PAIRS)}"
            )
            
        self.src_nllb = NLLB_LANG_MAP[self.src_lang]
        self.tgt_nllb = NLLB_LANG_MAP[self.tgt_lang]
        
        logger.info(
            f"[TranslationAgent] {self.src_lang} ({self.src_nllb}) → "
            f"{self.tgt_lang} ({self.tgt_nllb}) | model={self.model_id}"
        )

    def _load_model(self):
        """Lazy-load NLLB tokenizer and model."""
        if self._model is None:
            from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
            logger.info(f"[TranslationAgent] Loading model '{self.model_id}'...")
            
            # Initialize tokenizer with the source language
            self._tokenizer = AutoTokenizer.from_pretrained(
                self.model_id,
                src_lang=self.src_nllb
            )
            
            # Initialize Seq2Seq model
            self._model = AutoModelForSeq2SeqLM.from_pretrained(self.model_id)
            
            # Map to target device
            device_str = f"cuda:{self.device}" if self.device >= 0 else "cpu"
            self._model = self._model.to(device_str)
            
            logger.info(f"[TranslationAgent] Model loaded on {device_str}.")
            
        return self._tokenizer, self._model

    def translate_text(self, text: str) -> str:
        """
        Translate a single string.

        Args:
            text: Source text.

        Returns:
            Translated string.
        """
        if not text.strip():
            return ""

        tokenizer, model = self._load_model()
        device_str = f"cuda:{self.device}" if self.device >= 0 else "cpu"
        
        inputs = tokenizer([text], return_tensors="pt", padding=True, truncation=True, max_length=512)
        # Move inputs to target device
        inputs = {k: v.to(device_str) for k, v in inputs.items()}
        
        # Get target language token ID
        tgt_lang_id = tokenizer.convert_tokens_to_ids(self.tgt_nllb)
        
        translated = model.generate(**inputs, forced_bos_token_id=tgt_lang_id)
        result = tokenizer.batch_decode(translated, skip_special_tokens=True)
        return result[0] if result else ""

    def translate_segments(
        self,
        segments: List[dict],
        batch_size: int = 8,
        translated_key: str = "translated_text",
    ) -> List[dict]:
        """
        Translate a list of transcript segments in batches.

        Args:
            segments:       List of segment dicts with 'text' key.
            batch_size:     Number of texts to translate at once.
            translated_key: Key name for the translated output in each segment.

        Returns:
            Segments enriched with the translated text key.
        """
        tokenizer, model = self._load_model()
        device_str = f"cuda:{self.device}" if self.device >= 0 else "cpu"
        texts = [seg.get("text", "") for seg in segments]
        translated_texts = []

        logger.info(f"[TranslationAgent] Translating {len(texts)} segments (batch={batch_size})...")
        tgt_lang_id = tokenizer.convert_tokens_to_ids(self.tgt_nllb)

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            non_empty = [t if t.strip() else " " for t in batch]

            inputs = tokenizer(
                non_empty, return_tensors="pt", padding=True, truncation=True, max_length=512
            )
            # Move inputs to target device
            inputs = {k: v.to(device_str) for k, v in inputs.items()}
            
            outputs = model.generate(**inputs, forced_bos_token_id=tgt_lang_id)
            decoded = tokenizer.batch_decode(outputs, skip_special_tokens=True)
            translated_texts.extend(decoded)
            logger.debug(f"[TranslationAgent] Processed batch {i // batch_size + 1}")

        result = []
        for seg, translated in zip(segments, translated_texts):
            result.append({**seg, translated_key: translated.strip()})

        logger.info("[TranslationAgent] Translation complete.")
        return result

    @staticmethod
    def list_supported_pairs() -> List[str]:
        """Return human-readable list of supported language pairs."""
        return [f"{src} → {tgt}" for src, tgt in SUPPORTED_PAIRS]
