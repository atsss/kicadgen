"""Pydantic v2 data models for component specifications."""

from pydantic import BaseModel, Field


class PinSpec(BaseModel):
    """Specification for a single pin."""

    number: str = Field(..., description="Pin number (e.g., '1', 'A1')")
    name: str = Field(..., description="Pin name (e.g., 'VCC', 'GND')")
    type: str = Field(..., description="Pin type (e.g., 'POWER', 'GND', 'SIGNAL')")


class MetaSpec(BaseModel):
    """Metadata about the extracted component."""

    part_number: str = Field(..., description="Component part number")
    package_type: str = Field(..., description="Package type (e.g., 'QFN', 'BGA')")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Extraction confidence (0.0-1.0)")


class FootprintSpec(BaseModel):
    """Footprint specification for KiCAD generation."""

    pin_count: int = Field(..., gt=0, description="Total number of pins")
    pins_per_side: int = Field(..., gt=0, description="Number of pins per side (for rectangular packages)")
    pitch_mm: float = Field(..., gt=0, description="Pin pitch in millimeters")
    pad_width_mm: float = Field(..., gt=0, description="Pad width in millimeters")
    pad_length_mm: float = Field(..., gt=0, description="Pad length in millimeters")
    body_width_mm: float = Field(..., gt=0, description="Package body width in millimeters")
    body_length_mm: float = Field(..., gt=0, description="Package body length in millimeters")
    pin1_location: str = Field(default="top-left", description="Location of pin 1 (e.g., 'top-left')")


class SymbolSpec(BaseModel):
    """Symbol specification for KiCAD generation."""

    reference: str = Field(default="U", description="Reference designator prefix")
    pins: list[PinSpec] = Field(..., description="List of pins in the symbol")


class ComponentSpec(BaseModel):
    """Complete specification for a component."""

    meta: MetaSpec
    footprint: FootprintSpec
    symbol: SymbolSpec
