"""Pydantic v2 data models for component specifications."""

from pydantic import BaseModel, Field


class PadSpec(BaseModel):
    """Specification for a single footprint pad."""

    number: str = Field(..., description="Pad number (e.g., '1', 'A1')")
    x_mm: float = Field(
        ..., description="Pad X coordinate in millimeters (origin at package center)"
    )
    y_mm: float = Field(
        ..., description="Pad Y coordinate in millimeters (origin at package center)"
    )
    width_mm: float | None = Field(default=None, description="Pad width in millimeters")
    length_mm: float | None = Field(
        default=None, description="Pad length in millimeters"
    )
    drill_mm: float | None = Field(
        default=None,
        description="Drill hole diameter in millimeters (for through-hole)",
    )
    shape: str = Field(
        default="rect",
        description="Pad shape (KiCAD token: 'rect', 'oval', 'circle', 'roundrect', 'trapezoid', 'custom')",
    )


class PinSpec(BaseModel):
    """Specification for a single symbol pin."""

    number: str = Field(..., description="Pin number (e.g., '1', 'A1')")
    name: str = Field(..., description="Pin name (e.g., 'VCC', 'GND')")
    type: str = Field(
        ...,
        description="Pin type (e.g., 'input', 'output', 'power_in', 'power_out', 'passive', 'bidirectional')",
    )
    side: str | None = Field(
        default=None, description="Symbol placement (left, right, top, bottom)"
    )
    unit: int = Field(
        default=1, description="Symbol unit index (for multi-unit components)"
    )


class ComponentInfo(BaseModel):
    """General information about the component."""

    name: str = Field(..., description="Human readable component name")
    manufacturer: str = Field(..., description="Manufacturer name")
    part_number: str = Field(..., description="Official part number")
    description: str | None = Field(
        default=None, description="Short functional description"
    )
    package_type: str = Field(..., description="Package name (e.g., SOIC-8, QFN-32)")
    datasheet_source: str | None = Field(
        default=None, description="Datasheet filename or URL"
    )


class MetadataSpec(BaseModel):
    """AI extraction metadata and traceability."""

    extraction_confidence: float = Field(
        ..., ge=0.0, le=1.0, description="AI confidence score (0.0-1.0)"
    )
    missing_fields: list[str] = Field(
        default_factory=list, description="Fields not found in datasheet"
    )
    assumptions: list[str] = Field(
        default_factory=list, description="Any inferred values and assumptions"
    )
    source_pages: list[int] = Field(
        default_factory=list, description="Datasheet page numbers used"
    )


class SymbolSpec(BaseModel):
    """Symbol specification for KiCAD generation."""

    pin_count: int = Field(..., gt=0, description="Total number of pins in symbol")
    pin_pitch_grid: float | None = Field(
        default=None,
        description="Pin pitch grid in millimeters (defaults to 2.54mm if null)",
    )
    reference_prefix: str | None = Field(
        default=None,
        description="Reference designator prefix (defaults to 'U' if null)",
    )
    pins: list[PinSpec] = Field(..., description="List of pins in the symbol")


class FootprintSpec(BaseModel):
    """Footprint specification for KiCAD generation."""

    pin_count: int = Field(..., gt=0, description="Total number of pads")
    pins_per_side: int | None = Field(
        default=None, description="Number of pins per side (for rectangular packages)"
    )
    pad_type: str = Field(..., description="Pad type (smd or through_hole)")
    pad_shape: str = Field(
        default="rect",
        description="Default pad shape (KiCAD token: 'rect', 'oval', 'circle', 'roundrect', 'trapezoid', 'custom')",
    )
    pitch_mm: float | None = Field(default=None, description="Pin pitch in millimeters")
    pads: list[PadSpec] = Field(
        default_factory=list, description="Explicit pad coordinates and dimensions"
    )
    body_width_mm: float | None = Field(
        default=None, description="Package body width in millimeters"
    )
    body_length_mm: float | None = Field(
        default=None, description="Package body length in millimeters"
    )
    body_height_mm: float | None = Field(
        default=None, description="Package body height in millimeters"
    )
    pin1_location: str | None = Field(
        default=None, description="Location of pin 1 (e.g., 'top-left')"
    )


class ComponentSpec(BaseModel):
    """Complete specification for a component."""

    component: ComponentInfo
    symbol: SymbolSpec
    footprint: FootprintSpec
    metadata: MetadataSpec
