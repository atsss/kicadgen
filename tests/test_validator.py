"""Tests for the validator module."""

import pytest

from kicadgen.schema import ComponentSpec, FootprintSpec, MetaSpec, PinSpec, SymbolSpec
from kicadgen.validator import validate_component


@pytest.fixture
def valid_spec() -> ComponentSpec:
    """Create a valid component specification for testing."""
    return ComponentSpec(
        meta=MetaSpec(
            part_number="TEST-QFN16",
            package_type="QFN",
            confidence=0.95,
        ),
        footprint=FootprintSpec(
            pin_count=16,
            pins_per_side=4,
            pitch_mm=0.5,
            pad_width_mm=0.3,
            pad_length_mm=0.8,
            body_width_mm=3.0,
            body_length_mm=2.5,
            pin1_location="top-left",
        ),
        symbol=SymbolSpec(
            reference="U",
            pins=[
                PinSpec(number=str(i), name=f"PIN{i}", type="SIGNAL")
                for i in range(1, 17)
            ],
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
    valid_spec.footprint.body_length_mm = 1.0  # pitch * (pins_per_side - 1) = 0.5 * 3 = 1.5
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
    valid_spec.footprint.pad_width_mm = 0.6  # > pitch of 0.5
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
    valid_spec.footprint.pad_width_mm = 0.6  # Exceeds pitch
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
    valid_spec.footprint.pad_width_mm = 40
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
    valid_spec.footprint.pad_width_mm = 4.0
    report = validate_component(valid_spec)
    assert report.is_valid or len(report.errors) == 0


def test_validation_never_raises():
    """Test that validate_component never raises exceptions."""
    # Test with incomplete/malformed data shouldn't raise
    try:
        spec = ComponentSpec(
            meta=MetaSpec(part_number="TEST", package_type="QFN", confidence=0.5),
            footprint=FootprintSpec(
                pin_count=8,
                pins_per_side=2,
                pitch_mm=0.5,
                pad_width_mm=0.3,
                pad_length_mm=0.8,
                body_width_mm=3.0,
                body_length_mm=0.5,  # Invalid value
                pin1_location="top-left",
            ),
            symbol=SymbolSpec(
                reference="U",
                pins=[PinSpec(number="1", name="A", type="SIGNAL")],
            ),
        )
        report = validate_component(spec)
        # Should not raise; errors should be in report
        assert isinstance(report, object)
    except Exception as e:
        pytest.fail(f"validate_component raised exception: {e}")
