"""
Model Router Module
--------------------
Orchestrates and routes translation requests between NLLB-200 and the PEFT/LoRA adapter.
Exposes switchable backend methods: use_nllb(), use_lora(), and auto().
Provides compatibility interface to replace TranslationAgent inside the pipeline.
"""

import logging
from typing import List
from agents.translation_agent import TranslationAgent
from agents.localization_model import LocalizationModel

logger = logging.getLogger(__name__)

class ModelRouter:
    """
    Routing layer for CineLocalAI translation backends.
    Allows runtime or config-based switching between NLLB (default) and Mixtral + LoRA.
    """

    def __init__(self, config: dict):
        self.config = config
        
        # Load backend configurations safely
        loc_cfg = config.get("localization", {})
        if not isinstance(loc_cfg, dict):
            # Safe fallback if config format is flat
            self.backend = config.get("localization_backend", "nllb")
        else:
            self.backend = loc_cfg.get("backend", "nllb")
            
        models_cfg = config.get("models", {})
        if not isinstance(models_cfg, dict):
            self.lora_path = config.get("lora_path", "models/adaption_mixtral_lora")
            self.base_model = config.get("base_model", "mistralai/Mixtral-8x7B-Instruct-v0.1")
        else:
            self.lora_path = models_cfg.get("lora_path", "models/adaption_mixtral_lora")
            self.base_model = models_cfg.get("base_model", "mistralai/Mixtral-8x7B-Instruct-v0.1")

        logger.info(f"[ModelRouter] Initializing with backend: '{self.backend}'")

        # Initialize both translation adapters
        self.nllb_agent = TranslationAgent(
            src_lang=config.get("src_lang", "en"),
            tgt_lang=config.get("tgt_lang", "hi"),
            device=config.get("translation_device", -1)
        )
        self.lora_agent = LocalizationModel(
            lora_path=self.lora_path,
            base_model=self.base_model
        )

    def use_nllb(self):
        """Force the router to use the local Seq2Seq NLLB-200 backend."""
        self.backend = "nllb"
        logger.info("[ModelRouter] Forced backend route: NLLB-200")

    def use_lora(self):
        """Force the router to use the PEFT/LoRA adapter backend (runs in compatibility mode)."""
        self.backend = "lora"
        logger.info("[ModelRouter] Forced backend route: Mixtral + LoRA (PEFT)")

    def auto(self):
        """Dynamically route based on adapter availability (currently defaults to NLLB with a warning)."""
        self.backend = "auto"
        logger.info("[ModelRouter] Enabled dynamic auto-routing.")

    def translate_text(self, text: str) -> str:
        """Route translation of a single string based on current backend settings."""
        active_backend = self.backend.lower() if self.backend else "nllb"
        
        if active_backend == "auto":
            # Auto-route logic: Check if adapter is present and path valid
            if self.lora_agent.adapter_available:
                active_backend = "lora"
            else:
                active_backend = "nllb"
                
        if active_backend == "lora":
            return self.lora_agent.translate(
                text=text,
                source_lang=self.nllb_agent.src_lang,
                target_lang=self.nllb_agent.tgt_lang
            )
        else:
            return self.nllb_agent.translate_text(text)

    def translate_segments(
        self,
        segments: List[dict],
        batch_size: int = 8,
        translated_key: str = "translated_text"
    ) -> List[dict]:
        """Route translation of segment batches."""
        active_backend = self.backend.lower() if self.backend else "nllb"
        
        if active_backend == "auto":
            if self.lora_agent.adapter_available:
                active_backend = "lora"
            else:
                active_backend = "nllb"
                
        if active_backend == "lora":
            logger.warning(
                f"[ModelRouter] Routing {len(segments)} segments through LoRA adapter backend compatibility layer."
            )
            result = []
            for seg in segments:
                text = seg.get("text", "")
                emotion = seg.get("emotion")
                # Retrieve translation via LoRA model (which falls back to NLLB under constraints)
                translated = self.lora_agent.translate(
                    text=text,
                    source_lang=self.nllb_agent.src_lang,
                    target_lang=self.nllb_agent.tgt_lang,
                    emotion=emotion
                )
                result.append({**seg, translated_key: translated.strip()})
            return result
        else:
            return self.nllb_agent.translate_segments(
                segments=segments,
                batch_size=batch_size,
                translated_key=translated_key
            )
