"""VLM-based extraction of component specifications from datasheet images."""

import json
from typing import Any

from kicadgen.schema import ComponentSpec
from kicadgen.vlm_client import VLMClient


class ExtractionError(Exception):
    """Raised when extraction fails after all retries."""

    pass


def build_prompt(part_number: str) -> str:
    """
    Build the VLM prompt for component specification extraction.

    Args:
        part_number: Component part number for context

    Returns:
        Formatted prompt string
    """
    json_schema = """{
  "meta": {
    "part_number": "string (e.g., 'STM32H743')",
    "package_type": "string (e.g., 'QFN', 'BGA')",
    "confidence": "number between 0.0 and 1.0"
  },
  "footprint": {
    "pin_count": "integer (total number of pins)",
    "pins_per_side": "integer (for rectangular packages)",
    "pitch_mm": "number (pin pitch in millimeters)",
    "pad_width_mm": "number (pad width in millimeters)",
    "pad_length_mm": "number (pad length in millimeters)",
    "body_width_mm": "number (body width in millimeters)",
    "body_length_mm": "number (body length in millimeters)",
    "pin1_location": "string (e.g., 'top-left')"
  },
  "symbol": {
    "reference": "string (default 'U')",
    "pins": [
      {
        "number": "string (pin number, e.g., '1')",
        "name": "string (pin name, e.g., 'VCC')",
        "type": "string (pin type, e.g., 'POWER', 'GND', 'SIGNAL')"
      }
    ]
  }
}"""

    prompt = f"""You are a precision engineering assistant specializing in KiCAD component specifications.

Your task is to extract component specifications from the provided datasheet image(s) and return ONLY valid JSON (no markdown, no explanations).

**CRITICAL RULES:**
1. Return ONLY valid JSON - no markdown formatting, no "```json" wrappers, no explanations
2. All dimensions must be in MILLIMETERS (mm) - convert from mils, inches, or other units
3. Be precise: use actual values from the datasheet, never estimate or guess
4. Missing or unclear values must be null, not zero
5. confidence must be between 0.0 and 1.0 (0.8+ = high confidence, <0.8 = uncertainty)

**JSON Schema:**
{json_schema}

**Component Information:**
The component part number is: {part_number}

**Unit Conversion Notes:**
- If dimensions are in mils: divide by 1000 to get mm (e.g., 10 mils = 0.01 mm)
- If dimensions are in inches: multiply by 25.4 to get mm (e.g., 0.1" = 2.54 mm)
- If pitch/spacing shows in µm, divide by 1000 to get mm

**Output Format:**
Return ONLY the JSON object, starting with {{ and ending with }}, with no additional text.
"""

    return prompt


def parse_json_from_response(text: str) -> dict[str, Any]:
    """
    Parse JSON from VLM response, handling markdown formatting.

    Args:
        text: Raw response text from VLM

    Returns:
        Parsed JSON dictionary

    Raises:
        json.JSONDecodeError: If JSON is invalid
    """
    # Strip markdown code fences if present
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]  # Remove ```json
    elif text.startswith("```"):
        text = text[3:]  # Remove ```
    if text.endswith("```"):
        text = text[:-3]  # Remove trailing ```

    text = text.strip()
    return json.loads(text)


def extract(
    client: VLMClient,
    images: list[bytes],
    part_number: str,
    max_retries: int = 3,
) -> ComponentSpec:
    """
    Extract component specification from images using VLM.

    Args:
        client: VLMClient instance to use for extraction
        images: List of PNG image bytes from datasheet
        part_number: Component part number
        max_retries: Maximum number of extraction attempts

    Returns:
        ComponentSpec object

    Raises:
        ExtractionError: If extraction fails after all retries
    """
    prompt = build_prompt(part_number)

    last_error = None
    for attempt in range(max_retries):
        try:
            response = client.call(images, prompt)
            data = parse_json_from_response(response)
            spec = ComponentSpec(**data)
            return spec
        except (json.JSONDecodeError, ValueError) as e:
            last_error = e
            # Continue to next retry
            continue

    raise ExtractionError(
        f"Failed to extract component specification after {max_retries} attempts. "
        f"Last error: {last_error}"
    )
