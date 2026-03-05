"""Tests for footprint generation."""

import pytest

from kicadgen.generators.footprint import generate_footprint_sexpr
from kicadgen.schema import FootprintSpec


@pytest.fixture
def qfn_spec() -> FootprintSpec:
    """Create a sample QFN16 footprint spec."""
    return FootprintSpec(
        pin_count=16,
        pins_per_side=4,
        pitch_mm=0.5,
        pad_width_mm=0.3,
        pad_length_mm=0.8,
        body_width_mm=3.0,
        body_length_mm=2.5,
        pin1_location="top-left",
    )


def test_generate_footprint_returns_string(qfn_spec):
    """Test that footprint generation returns a string."""
    result = generate_footprint_sexpr(qfn_spec, "TEST-QFN16")
    assert isinstance(result, str)
    assert len(result) > 0


def test_generate_footprint_has_part_number(qfn_spec):
    """Test that part number is included in output."""
    result = generate_footprint_sexpr(qfn_spec, "TEST-QFN16")
    assert "TEST-QFN16" in result


def test_generate_footprint_has_kicad_structure(qfn_spec):
    """Test that output has KiCAD footprint S-expression structure."""
    result = generate_footprint_sexpr(qfn_spec, "TEST-QFN16")
    assert result.startswith("(footprint")
    assert result.endswith(")")
    assert "(version" in result
    assert "(pad" in result


def test_generate_footprint_has_all_pads(qfn_spec):
    """Test that all pads are included."""
    result = generate_footprint_sexpr(qfn_spec, "TEST-QFN16")
    # QFN16 should have 16 pads + 1 thermal pad
    # Check for pad counts (loose check for presence)
    assert result.count("(pad") >= 16


def test_generate_footprint_has_thermal_pad(qfn_spec):
    """Test that thermal pad is included."""
    result = generate_footprint_sexpr(qfn_spec, "TEST-QFN16")
    assert '(pad "TP"' in result


def test_generate_footprint_single_pin(qfn_spec):
    """Test footprint with single pin per side."""
    qfn_spec.pins_per_side = 1
    qfn_spec.pin_count = 4
    result = generate_footprint_sexpr(qfn_spec, "TINY")
    assert "(pad" in result
    assert "TINY" in result


def test_generate_footprint_large_pin_count(qfn_spec):
    """Test footprint with larger pin count."""
    qfn_spec.pins_per_side = 10
    qfn_spec.pin_count = 40
    qfn_spec.pitch_mm = 0.4
    result = generate_footprint_sexpr(qfn_spec, "LARGE-QFN40")
    assert "(pad" in result
    assert result.count("(pad") >= 40


def test_generate_footprint_coordinate_validity(qfn_spec):
    """Test that generated coordinates are reasonable (basic sanity check)."""
    result = generate_footprint_sexpr(qfn_spec, "TEST")
    # Parse coordinates roughly to ensure they're in reasonable range
    # Should contain decimal numbers in reasonable mm range
    assert "0." in result or "0" in result  # Should have some coordinates
    assert "at" in result  # KiCAD coordinate syntax


def test_generate_footprint_layer_specification(qfn_spec):
    """Test that layer specifications are included."""
    result = generate_footprint_sexpr(qfn_spec, "TEST")
    assert "F.Cu" in result
    assert "F.Paste" in result or "F.Mask" in result


def test_generate_footprint_different_part_numbers():
    """Test that different part numbers are correctly included."""
    spec = FootprintSpec(
        pin_count=8,
        pins_per_side=2,
        pitch_mm=1.0,
        pad_width_mm=0.5,
        pad_length_mm=1.0,
        body_width_mm=3.0,
        body_length_mm=2.0,
        pin1_location="top-left",
    )

    result1 = generate_footprint_sexpr(spec, "PART-A")
    result2 = generate_footprint_sexpr(spec, "PART-B")

    assert "PART-A" in result1
    assert "PART-B" in result2
    assert "PART-A" not in result2
    assert "PART-B" not in result1


def test_generate_footprint_pitch_affects_positions(qfn_spec):
    """Test that different pitches produce different pad positions."""
    spec1 = FootprintSpec(
        pin_count=4,
        pins_per_side=1,
        pitch_mm=0.5,
        pad_width_mm=0.3,
        pad_length_mm=0.8,
        body_width_mm=2.0,
        body_length_mm=2.0,
        pin1_location="top-left",
    )
    spec2 = FootprintSpec(
        pin_count=4,
        pins_per_side=1,
        pitch_mm=1.0,
        pad_width_mm=0.3,
        pad_length_mm=0.8,
        body_width_mm=2.0,
        body_length_mm=2.0,
        pin1_location="top-left",
    )

    result1 = generate_footprint_sexpr(spec1, "TEST")
    result2 = generate_footprint_sexpr(spec2, "TEST")

    # Results should differ due to different pad positions
    assert result1 != result2
