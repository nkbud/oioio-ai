"""
LLM client utilities for interacting with OpenRouter.
"""

import logging
import os
from typing import Dict, List, Any, Optional

import openai


class LLMClient:
    """Client for interacting with Large Language Models via OpenRouter."""

    def __init__(self, 
                 api_key: Optional[str] = None,
                 default_model: str = "gemini-2.0-flash-lite"):
        """
        Initialize the LLM client using OpenRouter.
        
        Args:
            api_key: API key for OpenRouter. If None, tries to use env var OPENROUTER_API_KEY
            default_model: Default model to use with OpenRouter
        """
        self.logger = logging.getLogger("llm_client")
        self.default_model = default_model
        
        # Configure OpenRouter client
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        if self.api_key:
            # OpenRouter supports the OpenAI client library with a different base URL
            self.client = openai.OpenAI(
                api_key=self.api_key,
                base_url="https://openrouter.ai/api/v1",
                default_headers={"HTTP-Referer": "https://github.com/nkbud/oioio-ai"}
            )
            self.logger.info(f"OpenRouter client configured with default model: {self.default_model}")
        else:
            self.client = None
            self.logger.warning("No OpenRouter API key provided. LLM features will be disabled.")

    def generate_completion(self, 
                           system_message: str,
                           user_message: str,
                           model: Optional[str] = None,
                           temperature: float = 0.5,
                           max_tokens: int = 1000) -> Optional[str]:
        """
        Generate a completion using the OpenRouter API.
        
        Args:
            system_message: System message for the LLM
            user_message: User message for the LLM
            model: LLM model to use, defaults to self.default_model
            temperature: Temperature for generation (0.0-1.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text or None if an error occurred
        """
        if not self.client:
            self.logger.warning("LLM client not configured. Cannot generate completion.")
            return None
            
        try:
            response = self.client.chat.completions.create(
                model=model or self.default_model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            self.logger.error(f"Error generating completion: {e}")
            return None
        
    def is_available(self) -> bool:
        """Check if the LLM client is available and configured."""
        return self.client is not None