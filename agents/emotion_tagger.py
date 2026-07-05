"""
Emotion Tagger Agent
--------------------
Analyzes transcript segments and tags each with an emotion label
and intensity score. Works entirely offline using a local
transformer model (j-hartmann/emotion-english-distilroberta-base).
"""

import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

# Mapping from model labels → cinematic emotion vocabulary
EMOTION_MAP = {
    "joy":      "joyful",
    "sadness":  "melancholic",
    "anger":    "intense",
    "fear":     "tense",
    "disgust":  "grim",
    "surprise": "surprising",
    "neutral":  "neutral",
}


class EmotionTagger:
    """
    Tags each transcript segment with an emotion label and confidence score.
    Uses a local HuggingFace model for fully offline inference.
    """

    DEFAULT_MODEL = "j-hartmann/emotion-english-distilroberta-base"

    def __init__(self, model_name: Optional[str] = None, device: int = -1):
        """
        Args:
            model_name: HuggingFace model ID (defaults to distilroberta emotion model).
            device:     -1 for CPU, 0+ for CUDA GPU index.
        """
        self.model_name = model_name or self.DEFAULT_MODEL
        self.device = device
        self._pipeline = None
        logger.info(f"[EmotionTagger] Initialized | model={self.model_name}")

    def _load_pipeline(self):
        """Lazy-load the HuggingFace text-classification pipeline."""
        if self._pipeline is None:
            from transformers import pipeline as hf_pipeline
            logger.info(f"[EmotionTagger] Loading model '{self.model_name}'...")
            self._pipeline = hf_pipeline(
                "text-classification",
                model=self.model_name,
                top_k=1,
                device=self.device,
            )
            logger.info("[EmotionTagger] Model ready.")
        return self._pipeline

    def tag_segment(self, text: str) -> dict:
        """
        Tag a single text segment with emotion.

        Args:
            text: The text to classify.

        Returns:
            dict with 'label', 'cinematic_label', 'score'
        """
        if not text.strip():
            return {"label": "neutral", "cinematic_label": "neutral", "score": 1.0}

        pipe = self._load_pipeline()
        results = pipe(text[:512])  # Truncate to model max length
        top = results[0][0] if isinstance(results[0], list) else results[0]

        raw_label = top["label"].lower()
        return {
            "label": raw_label,
            "cinematic_label": EMOTION_MAP.get(raw_label, "neutral"),
            "score": round(top["score"], 4),
        }

    def tag_transcript(self, segments: List[dict]) -> List[dict]:
        """
        Tag all segments in a transcript.

        Args:
            segments: List of segment dicts with at least a 'text' key.

        Returns:
            List of segments enriched with 'emotion' key (dict from tag_segment).
        """
        logger.info(f"[EmotionTagger] Tagging {len(segments)} segments...")
        tagged = []
        for i, seg in enumerate(segments):
            emotion = self.tag_segment(seg.get("text", ""))
            tagged.append({**seg, "emotion": emotion})
            if (i + 1) % 10 == 0:
                logger.debug(f"[EmotionTagger] Tagged {i + 1}/{len(segments)}")

        logger.info("[EmotionTagger] Emotion tagging complete.")
        return tagged

    def summarize_emotions(self, tagged_segments: List[dict]) -> dict:
        """
        Produce an overall emotion summary across all segments.

        Returns:
            dict mapping cinematic_label → cumulative score weight
        """
        summary: dict = {}
        for seg in tagged_segments:
            emotion = seg.get("emotion", {})
            label = emotion.get("cinematic_label", "neutral")
            score = emotion.get("score", 0.0)
            summary[label] = round(summary.get(label, 0.0) + score, 4)

        total = sum(summary.values()) or 1.0
        normalized = {k: round(v / total, 4) for k, v in summary.items()}
        dominant = max(normalized, key=normalized.get) if normalized else "neutral"

        return {
            "distribution": normalized,
            "dominant_emotion": dominant,
        }
