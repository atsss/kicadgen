"""VLM API client implementations for different providers."""

import base64
import os
from abc import ABC, abstractmethod
from typing import Any

import anthropic
import google.generativeai as genai
import openai


class VLMClient(ABC):
    """Abstract base class for VLM clients."""

    @abstractmethod
    def call(self, images: list[bytes], prompt: str) -> str:
        """
        Call the VLM API with images and a prompt.

        Args:
            images: List of PNG image bytes
            prompt: Text prompt for the VLM

        Returns:
            String response from the VLM
        """
        pass


class OpenAIClient(VLMClient):
    """OpenAI GPT-4o client."""

    def __init__(self):
        """Initialize OpenAI client with API key from environment."""
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        self.client = openai.OpenAI(api_key=api_key)

    def call(self, images: list[bytes], prompt: str) -> str:
        """Call GPT-4o with images and prompt."""
        # Encode images as base64
        image_contents = []
        for image_bytes in images:
            b64_image = base64.b64encode(image_bytes).decode("utf-8")
            image_contents.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{b64_image}",
                    },
                }
            )

        # Add text prompt
        message_content = image_contents + [{"type": "text", "text": prompt}]

        response = self.client.chat.completions.create(
            model="gpt-4o",
            max_tokens=2048,
            messages=[
                {
                    "role": "user",
                    "content": message_content,
                }
            ],
        )

        return response.choices[0].message.content


class AnthropicClient(VLMClient):
    """Anthropic Claude 3.5 Sonnet client."""

    def __init__(self):
        """Initialize Anthropic client with API key from environment."""
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        self.client = anthropic.Anthropic(api_key=api_key)

    def call(self, images: list[bytes], prompt: str) -> str:
        """Call Claude 3.5 Sonnet with images and prompt."""
        # Prepare image content
        image_sources = []
        for image_bytes in images:
            b64_image = base64.b64encode(image_bytes).decode("utf-8")
            image_sources.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": b64_image,
                    },
                }
            )

        # Add text prompt
        content: list[Any] = image_sources + [{"type": "text", "text": prompt}]

        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2048,
            messages=[
                {
                    "role": "user",
                    "content": content,
                }
            ],
        )

        return response.content[0].text


class GeminiClient(VLMClient):
    """Google Gemini 1.5 Pro client."""

    def __init__(self):
        """Initialize Gemini client with API key from environment."""
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-1.5-pro")

    def call(self, images: list[bytes], prompt: str) -> str:
        """Call Gemini 1.5 Pro with images and prompt."""
        # Convert bytes to PIL Images for Gemini
        from PIL import Image
        from io import BytesIO

        image_objects = []
        for image_bytes in images:
            pil_image = Image.open(BytesIO(image_bytes))
            image_objects.append(pil_image)

        # Add text prompt
        content: list[Any] = image_objects + [prompt]

        response = self.model.generate_content(content)
        return response.text


def get_client(model: str) -> VLMClient:
    """
    Factory function to get the appropriate VLM client.

    Args:
        model: Model name or prefix (e.g., 'gpt-4o', 'claude', 'gemini')

    Returns:
        VLMClient instance

    Raises:
        ValueError: If model is not recognized
    """
    model_lower = model.lower()

    if model_lower.startswith("gpt"):
        return OpenAIClient()
    elif model_lower.startswith("claude"):
        return AnthropicClient()
    elif model_lower.startswith("gemini"):
        return GeminiClient()
    else:
        raise ValueError(f"Unknown model: {model}")
