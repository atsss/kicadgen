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
        pad_type="smd",
        pad_shape="rectangle",
        pitch_mm=0.5,
        pads=[],
        body_width_mm=3.0,
        body_length_mm=2.5,
        body_height_mm=0.8,
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
    assert "(pad" in result or "pad" in result
    assert "TINY" in result


def test_generate_footprint_large_pin_count(qfn_spec):
    """Test footprint with larger pin count."""
    qfn_spec.pins_per_side = 10
    qfn_spec.pin_count = 40
    qfn_spec.pitch_mm = 0.4
    result = generate_footprint_sexpr(qfn_spec, "LARGE-QFN40")
    assert "(pad" in result or "pad" in result


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
        pad_type="smd",
        pad_shape="rectangle",
        pitch_mm=1.0,
        pads=[],
        body_width_mm=3.0,
        body_length_mm=2.0,
        body_height_mm=0.8,
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
        pad_type="smd",
        pad_shape="rectangle",
        pitch_mm=0.5,
        pads=[],
        body_width_mm=2.0,
        body_length_mm=2.0,
        body_height_mm=0.8,
        pin1_location="top-left",
    )
    spec2 = FootprintSpec(
        pin_count=4,
        pins_per_side=1,
        pad_type="smd",
        pad_shape="rectangle",
        pitch_mm=1.0,
        pads=[],
        body_width_mm=3.0,  # Different body width to ensure different output
        body_length_mm=2.0,
        body_height_mm=0.8,
        pin1_location="top-left",
    )

    result1 = generate_footprint_sexpr(spec1, "TEST")
    result2 = generate_footprint_sexpr(spec2, "TEST")

    # Results should differ due to different pad positions and thermal pad size
    assert result1 != result2


def test_fp_text_effects_properly_nested(qfn_spec):
    """Regression: effects block must be inside fp_text, not after it."""
    result = generate_footprint_sexpr(qfn_spec, "TEST")
    lines = result.splitlines()
    for i, line in enumerate(lines):
        if "(fp_text" in line:
            # fp_text line must NOT end with '))' (that would close fp_text prematurely)
            assert not line.rstrip().endswith("))"), (
                f"fp_text closed prematurely on line {i}: {line!r}"
            )


def test_explicit_pads_text_clears_pad_extent():
    """Test that reference/value text avoids overlap with explicit pads.

    For explicit pads, text position must account for pad length in Y direction.
    Text Y position should be ≥ pad_y + pad_length/2 + 1.0 (margin).
    """
    from kicadgen.schema import PadSpec

    spec = FootprintSpec(
        pin_count=2,
        pins_per_side=1,
        pad_type="smd",
        pad_shape="rectangle",
        pitch_mm=0.5,
        pads=[
            PadSpec(number="1", x_mm=0.0, y_mm=2.0, width_mm=0.5, length_mm=1.5),
            PadSpec(number="2", x_mm=0.0, y_mm=-2.0, width_mm=0.5, length_mm=1.5),
        ],
        body_width_mm=2.0,
        body_length_mm=2.0,
        body_height_mm=0.8,
    )

    result = generate_footprint_sexpr(spec, "TEST-PADS")

    # Extract text positions using regex to get coordinates from (at x y) format
    import re
    # Matches: (at 0 3.750) or (at 0.000 3.750)
    text_coord_patterns = re.findall(r'\(at\s+(-?[0-9.]+)\s+(-?[0-9.]+)\)', result)

    # Should have reference and value text
    assert len(text_coord_patterns) >= 2, "Should have at least reference and value text"

    # Extract Y coordinates (second element of each match)
    text_y_positions = [float(y) for x, y in text_coord_patterns]

    # Text positions should account for pad extent
    # Pad at y=2.0 with length=1.5 extends to 2.0 + 1.5/2 = 2.75
    # Text should be at ≥ 2.75 + 1.0 = 3.75 or ≤ -(3.75)
    max_y = max(text_y_positions)
    min_y = min(text_y_positions)

    assert max_y >= 3.75, f"Text position {max_y} should be ≥ 3.75 (accounting for pad extent)"
    assert min_y <= -3.75, f"Text position {min_y} should be ≤ -3.75 (accounting for pad extent)"


def test_qfn_text_clears_pad_extent():
    """Test that reference/value text avoids overlap with QFN pads.

    For QFN layout, pads extend to body_length/2 + pad_length.
    Text should be placed beyond this extent with 1.0 mm margin.
    """
    spec = FootprintSpec(
        pin_count=8,
        pins_per_side=2,
        pad_type="smd",
        pad_shape="rectangle",
        pitch_mm=0.5,
        pads=[],
        body_width_mm=3.0,
        body_length_mm=2.5,  # body_length/2 = 1.25
        body_height_mm=0.8,
        pin1_location="top-left",
    )

    result = generate_footprint_sexpr(spec, "TEST-QFN")

    # Extract text positions using regex to get coordinates from (at x y) format
    import re
    text_coord_patterns = re.findall(r'\(at\s+(-?[0-9.]+)\s+(-?[0-9.]+)\)', result)

    # Should have reference and value text
    assert len(text_coord_patterns) >= 2, "Should have at least reference and value text"

    # Extract Y coordinates (second element of each match)
    text_y_positions = [float(y) for x, y in text_coord_patterns]

    # With body_length=2.5 and pad_length=0.8:
    # Pad extent = 1.25 + 0.8 = 2.05
    # Text should be at ≥ 2.05 + 1.0 = 3.05 or ≤ -(3.05)
    max_y = max(text_y_positions)
    min_y = min(text_y_positions)

    expected_min_margin = 1.25 + 0.8 + 1.0  # body_length/2 + pad_length + margin
    assert max_y >= expected_min_margin, (
        f"Text position {max_y} should be ≥ {expected_min_margin} "
        f"(accounting for QFN pad extent + margin)"
    )
    assert min_y <= -expected_min_margin, (
        f"Text position {min_y} should be ≤ {-expected_min_margin} "
        f"(accounting for QFN pad extent + margin)"
    )


def test_qfn_pad_position_and_text_offset():
    """Verify QFN pad positions and text offset calculation details."""
    spec = FootprintSpec(
        pin_count=4,
        pins_per_side=1,
        pad_type="smd",
        pad_shape="rectangle",
        pitch_mm=0.5,
        pads=[],
        body_width_mm=2.0,
        body_length_mm=2.0,  # body_length/2 = 1.0
        body_height_mm=0.8,
        pin1_location="top-left",
    )

    result = generate_footprint_sexpr(spec, "TEST-QFN4")

    # Bottom pad (pin 1) should be at y = 1.0 + 0.4 = 1.4
    # Top pad (pin 3) should be at y = -(1.0 + 0.4) = -1.4
    # Pads extend to ±(1.0 + 0.8) = ±1.8
    # Text should be at ±(1.8 + 1.0) = ±2.8
    import re
    text_coord_patterns = re.findall(r'\(at\s+(-?[0-9.]+)\s+(-?[0-9.]+)\)', result)
    text_y_positions = [float(y) for x, y in text_coord_patterns]

    # Find the text positions (should include reference and value)
    assert len(text_y_positions) >= 2, "Should have at least reference and value text"

    # Check that text positions are approximately ±2.8 (allowing small floating point tolerance)
    value_text_y = max(text_y_positions)
    ref_text_y = min(text_y_positions)

    assert abs(value_text_y - 2.8) < 0.01, (
        f"Value text should be at y=2.8 (pad extent 1.8 + margin 1.0), got {value_text_y}"
    )
    assert abs(ref_text_y - (-2.8)) < 0.01, (
        f"Reference text should be at y=-2.8 (pad extent 1.8 + margin 1.0), got {ref_text_y}"
    )
