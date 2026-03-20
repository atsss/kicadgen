"""VLM-based extraction of component specifications from datasheet images."""

import json
import logging
from typing import Any

from kicadgen.schema import ComponentSpec
from kicadgen.vlm_client import VLMClient

logger = logging.getLogger(__name__)


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
  "component": {
    "name": "string (e.g., 'STM32H743 Microcontroller')",
    "manufacturer": "string (e.g., 'STMicroelectronics')",
    "part_number": "string (official part number)",
    "description": "string (short functional description)",
    "package_type": "string (e.g., 'QFN-32', 'SOIC-8')",
    "datasheet_source": "string (filename or URL)"
  },
  "symbol": {
    "pin_count": "integer (total number of pins)",
    "pin_pitch_grid": "number (grid spacing in mm, default 2.54)",
    "reference_prefix": "string (e.g., 'U' for IC, 'R' for resistor)",
    "pins": [
      {
        "number": "string (pin number from datasheet)",
        "name": "string (pin name, e.g., 'VCC', 'GND')",
        "type": "string (input, output, passive, power_in, power_out, bidirectional)",
        "side": "string or null (left, right, top, bottom for placement hint)",
        "unit": "integer (symbol unit index, default 1)"
      }
    ]
  },
  "footprint": {
    "pin_count": "integer (total number of pads)",
    "pins_per_side": "integer or null (for rectangular packages)",
    "pad_type": "string (smd or through_hole)",
    "pad_shape": "string (rectangle, oval, circle)",
    "pitch_mm": "number or null (pin pitch in millimeters)",
    "pads": [
      {
        "number": "string (pad number)",
        "x_mm": "number (x coordinate, origin at package center)",
        "y_mm": "number (y coordinate, origin at package center)",
        "width_mm": "number or null (pad width in mm)",
        "length_mm": "number or null (pad length in mm)",
        "drill_mm": "number or null (drill diameter for through-hole)",
        "shape": "string (pad shape)"
      }
    ],
    "body_width_mm": "number or null (package width in mm)",
    "body_length_mm": "number or null (package length in mm)",
    "body_height_mm": "number or null (package height in mm)",
    "pin1_location": "string or null (location of pin 1, e.g., 'top-left')"
  },
  "metadata": {
    "extraction_confidence": "number between 0.0 and 1.0 (0.8+ = high, <0.8 = uncertain)",
    "missing_fields": ["list of field names not found in datasheet"],
    "assumptions": ["list of values that were inferred or assumed"],
    "source_pages": "[list of page numbers used from datasheet]"
  }
}"""

    prompt = f"""You are a precision engineering assistant specializing in KiCAD component specifications.

Your task is to extract component specifications from the provided datasheet image(s) and return ONLY valid JSON (no markdown, no explanations).

**CRITICAL RULES:**
1. Return ONLY valid JSON - no markdown formatting, no "```json" wrappers, no explanations
2. All dimensions must be in MILLIMETERS (mm) - convert from mils, inches, or other units
3. Be precise: use actual values from the datasheet, NEVER estimate or guess
4. Missing or unclear values must be null, never zero or guessed
5. extraction_confidence must be between 0.0 and 1.0 (0.8+ = high confidence, <0.8 = uncertainty)
6. List ALL missing fields in metadata.missing_fields
7. Document any assumptions or inferred values in metadata.assumptions

**JSON Schema:**
{json_schema}

**IMPORTANT FIELD CATEGORIZATION:**

CRITICAL FIELDS (must always be extracted, never null):
- component.name: Component model/part name
- component.part_number: Part identifier
- component.manufacturer: Manufacturer name
- component.package_type: Package type (QFN, DIP, SOIC, etc.)
- symbol.pin_count: Total number of pins
- symbol.pins[]: Pin list with:
  - number: Pin identifier (1, 2, 3, A1, etc.)
  - name: Pin name (VCC, GND, DATA, CLK, etc.)
  - type: Pin type (input, output, power_in, power_out, passive, bidirectional)
- footprint.pin_count: Total pins for footprint
- footprint.pad_type: Either "smd" or "through_hole"

FIELDS WITH SYSTEM DEFAULTS (can be null, system will fill them):
- symbol.pin_pitch_grid: Defaults to 2.54mm if null
- symbol.reference_prefix: Defaults to "U" if null
- component.description: Can be null (optional metadata)
- component.datasheet_source: Can be null (optional metadata)

FIELDS THAT CAN BE NULL (geometric/optional):
- footprint.pitch_mm, body_width_mm, body_length_mm, pins_per_side
- All other footprint fields and pad details

If a critical field is truly unclear from the datasheet, document it in metadata.missing_fields and metadata.assumptions, but still provide your best extraction attempt.

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


def apply_schema_defaults(data: dict[str, Any]) -> dict[str, Any]:
    """Apply schema-defined defaults to extracted data before Pydantic validation.

    Fields that the LLM may return as null but the system has defaults for:
    - symbol.pin_pitch_grid defaults to 2.54mm
    - symbol.reference_prefix defaults to "U"

    Args:
        data: Extracted data dictionary with potentially null optional fields

    Returns:
        Dictionary with defaults applied to null fields
    """
    if "symbol" in data:
        if data["symbol"].get("pin_pitch_grid") is None:
            data["symbol"]["pin_pitch_grid"] = 2.54
            logger.debug("Applied default pin_pitch_grid: 2.54mm")
        if data["symbol"].get("reference_prefix") is None:
            data["symbol"]["reference_prefix"] = "U"
            logger.debug("Applied default reference_prefix: U")

    return data


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
    return json.loads(text)  # type: ignore[no-any-return]


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

    last_error: json.JSONDecodeError | ValueError | None = None
    for attempt in range(max_retries):
        logger.debug(
            f"Extraction attempt {attempt + 1}/{max_retries} for {part_number}"
        )
        try:
            response = client.call(images, prompt)
            data = parse_json_from_response(response)
            # Apply schema-defined defaults before validation
            data = apply_schema_defaults(data)
            spec = ComponentSpec(**data)
            logger.debug(f"Extraction succeeded on attempt {attempt + 1}")
            return spec
        except json.JSONDecodeError as e:
            last_error = e
            logger.debug(f"Attempt {attempt + 1}: JSON parse error: {e}")
            continue
        except ValueError as e:
            last_error = e
            logger.debug(f"Attempt {attempt + 1}: Schema validation error: {e}")
            continue

    logger.error(f"Failed to extract after {max_retries} attempts for {part_number}")
    raise ExtractionError(
        f"Failed to extract component specification after {max_retries} attempts. "
        f"Last error: {last_error}"
    )
