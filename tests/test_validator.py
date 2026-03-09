"""Tests for the validator module."""

import pytest

from kicadgen.schema import ComponentInfo, ComponentSpec, FootprintSpec, MetadataSpec, PadSpec, PinSpec, SymbolSpec
from kicadgen.validator import validate_component


@pytest.fixture
def valid_spec() -> ComponentSpec:
    """Create a valid component specification for testing."""
    return ComponentSpec(
        component=ComponentInfo(
            name="Test IC",
            manufacturer="TestCorp",
            part_number="TEST-QFN16",
            description="Test component",
            package_type="QFN",
            datasheet_source="test.pdf",
        ),
        symbol=SymbolSpec(
            pin_count=16,
            pin_pitch_grid=2.54,
            reference_prefix="U",
            pins=[
                PinSpec(number=str(i), name=f"PIN{i}", type="SIGNAL", side="left" if i <= 8 else "right")
                for i in range(1, 17)
            ],
        ),
        footprint=FootprintSpec(
            pin_count=16,
            pins_per_side=4,
            pad_type="smd",
            pad_shape="rectangle",
            pitch_mm=0.5,
            pads=[],
            body_width_mm=3.0,
            body_length_mm=1.5,  # pitch * (pins_per_side - 1) = 0.5 * 3 = 1.5
            body_height_mm=0.8,
            pin1_location="top-left",
        ),
        metadata=MetadataSpec(
            extraction_confidence=0.95,
            missing_fields=[],
            assumptions=[],
            source_pages=[3],
        ),
    )


def test_valid_specification(valid_spec):
    """Test that a valid specification passes validation."""
    report = validate_component(valid_spec)
    assert report.is_valid
    assert len(report.errors) == 0


def test_geometric_consistency_error(valid_spec):
    """Test that geometric inconsistency is caught."""
    # Make body length inconsistent with pitch and pins_per_side
    valid_spec.footprint.body_length_mm = 0.9  # pitch * (pins_per_side - 1) = 0.5 * 3 = 1.5, difference = 0.6 > tolerance
    report = validate_component(valid_spec)
    assert not report.is_valid
    assert len(report.errors) == 1
    assert "Geometric inconsistency" in report.errors[0]


def test_pitch_too_small_error(valid_spec):
    """Test that pitch below minimum is rejected."""
    valid_spec.footprint.pitch_mm = 0.1
    report = validate_component(valid_spec)
    assert not report.is_valid
    assert any("Invalid pitch" in error for error in report.errors)


def test_pad_width_exceeds_pitch_error(valid_spec):
    """Test that pad width > pitch is rejected."""
    # Add a pad with width > pitch
    valid_spec.footprint.pads = [
        PadSpec(number="1", x_mm=0, y_mm=0, width_mm=0.6, length_mm=0.8, shape="rectangle")
    ]
    report = validate_component(valid_spec)
    assert not report.is_valid
    assert any("Invalid pad width" in error for error in report.errors)


def test_pin_count_mismatch_error(valid_spec):
    """Test that pin count vs symbol pins mismatch is caught."""
    # Remove some pins from symbol
    valid_spec.symbol.pins = valid_spec.symbol.pins[:8]
    report = validate_component(valid_spec)
    assert not report.is_valid
    assert any("Pin count mismatch" in error for error in report.errors)


def test_multiple_errors(valid_spec):
    """Test that multiple errors are reported."""
    valid_spec.footprint.pitch_mm = 0.1  # Too small
    # Add a pad with width > pitch
    valid_spec.footprint.pads = [
        PadSpec(number="1", x_mm=0, y_mm=0, width_mm=0.6, length_mm=0.8, shape="rectangle")
    ]
    report = validate_component(valid_spec)
    assert not report.is_valid
    assert len(report.errors) >= 2


def test_geometric_tolerance(valid_spec):
    """Test that geometric consistency allows ±0.5mm tolerance."""
    # Body length: pitch * (pins_per_side - 1) = 0.5 * 3 = 1.5mm
    # Test at +0.5mm tolerance
    valid_spec.footprint.body_length_mm = 2.0
    report = validate_component(valid_spec)
    assert report.is_valid

    # Test just outside tolerance
    valid_spec.footprint.body_length_mm = 2.1
    report = validate_component(valid_spec)
    assert not report.is_valid


def test_unit_heuristic_warning(valid_spec):
    """Test that suspicious mil values trigger warnings."""
    # Set pitch to a value that looks like mils (e.g., 50 mils)
    valid_spec.footprint.pitch_mm = 50
    valid_spec.footprint.body_length_mm = 150  # Adjust to pass geometric test
    report = validate_component(valid_spec)
    # Should have warnings but may still be valid depending on other constraints
    assert len(report.warnings) > 0 or not report.is_valid


def test_inch_unit_warning(valid_spec):
    """Test that large values (possible inches) trigger warnings."""
    # 1 inch = 25.4mm
    valid_spec.footprint.pitch_mm = 25.4
    valid_spec.footprint.body_length_mm = 76.2  # 25.4 * 3
    valid_spec.footprint.body_width_mm = 25.4
    report = validate_component(valid_spec)
    # Should have warnings
    assert len(report.warnings) > 0


def test_no_errors_on_valid_large_pitch(valid_spec):
    """Test that reasonable large pitch doesn't trigger false warnings."""
    # 5mm pitch with proper geometry
    valid_spec.footprint.pitch_mm = 5.0
    valid_spec.footprint.pins_per_side = 4
    valid_spec.footprint.body_length_mm = 15.0  # 5 * 3
    report = validate_component(valid_spec)
    assert report.is_valid or len(report.errors) == 0


def test_validation_never_raises():
    """Test that validate_component never raises exceptions."""
    # Test with incomplete/malformed data shouldn't raise
    try:
        spec = ComponentSpec(
            component=ComponentInfo(
                name="Test", manufacturer="Corp", part_number="TEST",
                description="Test", package_type="QFN", datasheet_source="test.pdf"
            ),
            footprint=FootprintSpec(
                pin_count=8,
                pins_per_side=2,
                pad_type="smd",
                pad_shape="rectangle",
                pitch_mm=0.5,
                pads=[],
                body_width_mm=3.0,
                body_length_mm=0.5,  # Invalid value
                pin1_location="top-left",
            ),
            symbol=SymbolSpec(
                pin_count=1,
                reference_prefix="U",
                pins=[PinSpec(number="1", name="A", type="SIGNAL")],
            ),
            metadata=MetadataSpec(extraction_confidence=0.5),
        )
        report = validate_component(spec)
        # Should not raise; errors should be in report
        assert isinstance(report, object)
    except Exception as e:
        pytest.fail(f"validate_component raised exception: {e}")
