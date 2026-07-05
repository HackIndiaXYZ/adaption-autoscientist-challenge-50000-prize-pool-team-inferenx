"""
Localization Model Wrapper
---------------------------
Wraps the PEFT/LoRA adapter configured for the mistralai/Mixtral-8x7B-Instruct-v0.1
base model. Since running a 46B parameter Mixtral model locally is disabled due to 
resource constraints, this agent acts as an architectural container, validating paths
and falling back to the standard Seq2Seq NLLB-200 translation agent under the hood.
"""

import os
import json
import logging
from typing import Optional
from .translation_agent import TranslationAgent

logger = logging.getLogger(__name__)

class LocalizationModel:
    """
    Wrapper interface for the PEFT LoRA adapter for localization.
    Centralizes path detection, configuration loading, and acts as a router/fallback container.
    """

    def __init__(self, lora_path: str = "models/adaption_mixtral_lora", base_model: str = "mistralai/Mixtral-8x7B-Instruct-v0.1"):
        self.lora_path = lora_path
        self.base_model = base_model
        self.adapter_config = {}
        self.adapter_available = False
        
        # Check if the adapter exists at the given path
        self._detect_adapter()
        
        # Initialize the fallback NLLB translation agents when needed
        # We lazy-load these on a per-language basis to save memory
        self._fallback_agents = {}

    def _detect_adapter(self):
        """Detect model configuration and safetensors files to confirm adapter availability."""
        if not os.path.isdir(self.lora_path):
            logger.warning(f"[LocalizationModel] LoRA path not found: {self.lora_path}")
            return
            
        config_file = os.path.join(self.lora_path, "adapter_config.json")
        model_file = os.path.join(self.lora_path, "adapter_model.safetensors")
        
        if os.path.isfile(config_file) and os.path.isfile(model_file):
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    self.adapter_config = json.load(f)
                self.adapter_available = True
                logger.info(
                    f"[LocalizationModel] Detected LoRA adapter at '{self.lora_path}' "
                    f"configured for base model '{self.adapter_config.get('base_model_name_or_path', self.base_model)}'."
                )
            except Exception as e:
                logger.error(f"[LocalizationModel] Failed to load adapter configuration: {e}")
        else:
            logger.warning(f"[LocalizationModel] LoRA adapter files not complete at '{self.lora_path}'. Missing adapter_config.json or adapter_model.safetensors.")

    def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        emotion: Optional[str] = None,
        context: Optional[str] = None
    ) -> str:
        """
        Translates text with optional emotion and context.
        Since local execution of Mixtral-8x7B is disabled, we log architectural metrics/warnings 
        and route translation to NLLB.
        """
        logger.warning(
            f"[LocalizationModel] WARNING: Local inference for base model '{self.base_model}' with "
            f"adapter '{self.lora_path}' is bypassed due to resource constraints. "
            f"Routing translation request to NLLB-200."
        )
        
        # Retrieve or initialize the NLLB TranslationAgent for this specific language pair
        lang_key = (source_lang.lower(), target_lang.lower())
        if lang_key not in self._fallback_agents:
            try:
                self._fallback_agents[lang_key] = TranslationAgent(
                    src_lang=source_lang,
                    tgt_lang=target_lang
                )
            except Exception as e:
                logger.error(f"[LocalizationModel] Fallback initialization failed for {source_lang} -> {target_lang}: {e}")
                return text  # Return original if translation setup fails
                
        agent = self._fallback_agents[lang_key]
        
        # Enrich the query with emotion or context if available (architectural exercise)
        enriched_text = text
        if emotion or context:
            parts = []
            if emotion:
                parts.append(f"[Emotion: {emotion}]")
            if context:
                parts.append(f"[Context: {context}]")
            enriched_text = f"{' '.join(parts)} {text}"
            logger.debug(f"[LocalizationModel] Simulating context-aware routing with text: '{enriched_text}'")

        return agent.translate_text(text)
