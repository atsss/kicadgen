"""Tests for the extractor module."""

import json
from unittest.mock import MagicMock

import pytest

from kicadgen.extractor import ExtractionError, build_prompt, extract, parse_json_from_response
from kicadgen.schema import ComponentSpec


def test_build_prompt():
    """Test that build_prompt creates a valid prompt."""
    prompt = build_prompt("TEST-QFN16")
    assert "TEST-QFN16" in prompt
    assert "JSON" in prompt or "json" in prompt
    assert "millimeters" in prompt or "mm" in prompt
    assert isinstance(prompt, str)
    assert len(prompt) > 100  # Should be a detailed prompt


def test_parse_json_from_response_plain():
    """Test JSON parsing from plain response."""
    json_data = {"meta": {"part_number": "TEST", "package_type": "QFN", "confidence": 0.9}}
    response = json.dumps(json_data)
    parsed = parse_json_from_response(response)
    assert parsed == json_data


def test_parse_json_from_response_with_markdown():
    """Test JSON parsing with markdown code fences."""
    json_data = {"meta": {"part_number": "TEST", "package_type": "QFN", "confidence": 0.9}}
    response = "```json\n" + json.dumps(json_data) + "\n```"
    parsed = parse_json_from_response(response)
    assert parsed == json_data


def test_parse_json_from_response_with_plain_fence():
    """Test JSON parsing with plain code fence."""
    json_data = {"meta": {"part_number": "TEST", "package_type": "QFN", "confidence": 0.9}}
    response = "```\n" + json.dumps(json_data) + "\n```"
    parsed = parse_json_from_response(response)
    assert parsed == json_data


def test_parse_json_with_extra_whitespace():
    """Test JSON parsing with extra whitespace."""
    json_data = {"meta": {"part_number": "TEST", "package_type": "QFN", "confidence": 0.9}}
    response = "  \n" + json.dumps(json_data) + "  \n"
    parsed = parse_json_from_response(response)
    assert parsed == json_data


def test_parse_json_invalid():
    """Test that invalid JSON raises JSONDecodeError."""
    with pytest.raises(json.JSONDecodeError):
        parse_json_from_response("not valid json")


def test_extract_success():
    """Test successful extraction."""
    # Create mock client
    mock_client = MagicMock()
    valid_response = {
        "meta": {
            "part_number": "TEST-QFN16",
            "package_type": "QFN",
            "confidence": 0.95,
        },
        "footprint": {
            "pin_count": 16,
            "pins_per_side": 4,
            "pitch_mm": 0.5,
            "pad_width_mm": 0.3,
            "pad_length_mm": 0.8,
            "body_width_mm": 3.0,
            "body_length_mm": 2.5,
            "pin1_location": "top-left",
        },
        "symbol": {
            "reference": "U",
            "pins": [
                {"number": str(i), "name": f"PIN{i}", "type": "SIGNAL"}
                for i in range(1, 17)
            ],
        },
    }
    mock_client.call.return_value = json.dumps(valid_response)

    spec = extract(mock_client, [b"fake_image"], "TEST-QFN16", max_retries=3)

    assert isinstance(spec, ComponentSpec)
    assert spec.meta.part_number == "TEST-QFN16"
    assert spec.footprint.pin_count == 16


def test_extract_retry_on_invalid_json():
    """Test that extraction retries on invalid JSON."""
    mock_client = MagicMock()
    valid_response = {
        "meta": {
            "part_number": "TEST",
            "package_type": "QFN",
            "confidence": 0.9,
        },
        "footprint": {
            "pin_count": 8,
            "pins_per_side": 2,
            "pitch_mm": 0.5,
            "pad_width_mm": 0.3,
            "pad_length_mm": 0.8,
            "body_width_mm": 3.0,
            "body_length_mm": 1.5,
            "pin1_location": "top-left",
        },
        "symbol": {
            "reference": "U",
            "pins": [
                {"number": str(i), "name": f"PIN{i}", "type": "SIGNAL"}
                for i in range(1, 9)
            ],
        },
    }

    # First call returns invalid JSON, second call returns valid JSON
    mock_client.call.side_effect = [
        "invalid json {",
        json.dumps(valid_response),
    ]

    spec = extract(mock_client, [b"fake_image"], "TEST", max_retries=3)
    assert isinstance(spec, ComponentSpec)
    assert mock_client.call.call_count == 2


def test_extract_failure_after_max_retries():
    """Test that extraction raises ExtractionError after max retries."""
    mock_client = MagicMock()
    mock_client.call.return_value = "always invalid json {"

    with pytest.raises(ExtractionError):
        extract(mock_client, [b"fake_image"], "TEST", max_retries=2)

    assert mock_client.call.call_count == 2


def test_extract_with_markdown_response():
    """Test extraction handles markdown-wrapped JSON."""
    mock_client = MagicMock()
    valid_response = {
        "meta": {
            "part_number": "TEST",
            "package_type": "QFN",
            "confidence": 0.9,
        },
        "footprint": {
            "pin_count": 8,
            "pins_per_side": 2,
            "pitch_mm": 0.5,
            "pad_width_mm": 0.3,
            "pad_length_mm": 0.8,
            "body_width_mm": 3.0,
            "body_length_mm": 1.5,
            "pin1_location": "top-left",
        },
        "symbol": {
            "reference": "U",
            "pins": [
                {"number": str(i), "name": f"PIN{i}", "type": "SIGNAL"}
                for i in range(1, 9)
            ],
        },
    }
    markdown_response = "```json\n" + json.dumps(valid_response) + "\n```"
    mock_client.call.return_value = markdown_response

    spec = extract(mock_client, [b"fake_image"], "TEST")
    assert isinstance(spec, ComponentSpec)
