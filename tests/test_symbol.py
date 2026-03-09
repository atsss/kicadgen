"""Tests for symbol generation."""

import pytest

from kicadgen.generators.symbol import generate_symbol_sexpr
from kicadgen.schema import PinSpec, SymbolSpec


@pytest.fixture
def qfn_symbol() -> SymbolSpec:
    """Create a sample QFN16 symbol spec."""
    return SymbolSpec(
        pin_count=16,
        pin_pitch_grid=2.54,
        reference_prefix="U",
        pins=[
            PinSpec(number=str(i), name=f"PIN{i}", type="SIGNAL", side="left" if i <= 8 else "right", unit=1)
            for i in range(1, 17)
        ],
    )


def test_generate_symbol_returns_string(qfn_symbol):
    """Test that symbol generation returns a string."""
    result = generate_symbol_sexpr(qfn_symbol, "TEST-QFN16")
    assert isinstance(result, str)
    assert len(result) > 0


def test_generate_symbol_has_part_number(qfn_symbol):
    """Test that part number is included in output."""
    result = generate_symbol_sexpr(qfn_symbol, "TEST-QFN16")
    assert "TEST-QFN16" in result


def test_generate_symbol_has_kicad_structure(qfn_symbol):
    """Test that output has KiCAD symbol S-expression structure."""
    result = generate_symbol_sexpr(qfn_symbol, "TEST-QFN16")
    assert result.startswith("(symbol")
    assert result.endswith(")")
    assert "(pin" in result or "pin" in result.lower()


def test_generate_symbol_has_reference(qfn_symbol):
    """Test that reference designator is included."""
    result = generate_symbol_sexpr(qfn_symbol, "TEST")
    assert "U" in result


def test_generate_symbol_has_all_pins(qfn_symbol):
    """Test that all pins are included."""
    result = generate_symbol_sexpr(qfn_symbol, "TEST")
    # Should have 16 pins
    assert result.count("(pin") >= 16 or result.count("pin") >= 16


def test_generate_symbol_single_pin():
    """Test symbol with single pin."""
    symbol = SymbolSpec(
        pin_count=1,
        reference_prefix="U",
        pins=[PinSpec(number="1", name="VCC", type="POWER", unit=1)],
    )
    result = generate_symbol_sexpr(symbol, "SIMPLE")
    assert "VCC" in result
    assert "1" in result


def test_generate_symbol_pin_names_included(qfn_symbol):
    """Test that pin names are included in output."""
    result = generate_symbol_sexpr(qfn_symbol, "TEST")
    # Should contain some pin names
    assert "PIN1" in result


def test_generate_symbol_pin_numbers_included(qfn_symbol):
    """Test that pin numbers are included in output."""
    result = generate_symbol_sexpr(qfn_symbol, "TEST")
    # Should contain some pin numbers
    pin_nums_present = any(f'"{i}"' in result for i in range(1, 17))
    assert pin_nums_present


def test_generate_symbol_different_part_numbers():
    """Test that different part numbers are correctly included."""
    symbol = SymbolSpec(
        pin_count=1,
        reference_prefix="U",
        pins=[PinSpec(number="1", name="PIN", type="SIGNAL", unit=1)],
    )

    result1 = generate_symbol_sexpr(symbol, "PART-A")
    result2 = generate_symbol_sexpr(symbol, "PART-B")

    assert "PART-A" in result1
    assert "PART-B" in result2
    assert "PART-A" not in result2
    assert "PART-B" not in result1


def test_generate_symbol_large_pin_count():
    """Test symbol with large pin count."""
    pins = [
        PinSpec(number=str(i), name=f"PIN{i}", type="SIGNAL", unit=1)
        for i in range(1, 49)
    ]
    symbol = SymbolSpec(pin_count=48, reference_prefix="U", pins=pins)
    result = generate_symbol_sexpr(symbol, "BIG")

    assert "(pin" in result or "pin" in result.lower()
    assert result.count("(pin") >= 48 or "PIN1" in result


def test_generate_symbol_special_pin_types():
    """Test symbol with different pin types."""
    symbol = SymbolSpec(
        pin_count=4,
        reference_prefix="U",
        pins=[
            PinSpec(number="1", name="VCC", type="POWER", unit=1),
            PinSpec(number="2", name="GND", type="GND", unit=1),
            PinSpec(number="3", name="DATA", type="SIGNAL", unit=1),
            PinSpec(number="4", name="CLK", type="SIGNAL", unit=1),
        ],
    )
    result = generate_symbol_sexpr(symbol, "MIXED")

    # All pin names should be present
    for pin in symbol.pins:
        assert pin.name in result


def test_generate_symbol_reference_field():
    """Test that reference field is properly set."""
    symbol = SymbolSpec(
        pin_count=1,
        reference_prefix="IC",
        pins=[PinSpec(number="1", name="A", type="SIGNAL", unit=1)],
    )
    result = generate_symbol_sexpr(symbol, "TEST")
    assert "IC" in result


def test_generate_symbol_vs_different_pin_counts():
    """Test that different pin counts produce different outputs."""
    symbol_4 = SymbolSpec(
        pin_count=4,
        reference_prefix="U",
        pins=[
            PinSpec(number=str(i), name=f"PIN{i}", type="SIGNAL", unit=1)
            for i in range(1, 5)
        ],
    )
    symbol_8 = SymbolSpec(
        pin_count=8,
        reference_prefix="U",
        pins=[
            PinSpec(number=str(i), name=f"PIN{i}", type="SIGNAL", unit=1)
            for i in range(1, 9)
        ],
    )

    result_4 = generate_symbol_sexpr(symbol_4, "TEST")
    result_8 = generate_symbol_sexpr(symbol_8, "TEST")

    # Results should differ
    assert result_4 != result_8
    # 8-pin should have more content
    assert len(result_8) > len(result_4)
