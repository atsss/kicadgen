"""Validation of extracted component specifications."""

from dataclasses import dataclass, field

from kicadgen.schema import ComponentSpec


@dataclass
class ValidationReport:
    """Result of validating a component specification."""

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """Check if validation passed (no errors)."""
        return len(self.errors) == 0


def validate_component(spec: ComponentSpec) -> ValidationReport:
    """
    Validate a component specification according to project rules.

    Returns a ValidationReport with errors and warnings (never raises).
    """
    report = ValidationReport()

    # Rule 1: Geometric consistency
    # pitch_mm × (pins_per_side - 1) ≈ body_length_mm (tolerance ±0.5mm)
    # Only check if both values are provided
    if (spec.footprint.pitch_mm is not None and
        spec.footprint.pins_per_side is not None and
        spec.footprint.body_length_mm is not None):
        expected_length = spec.footprint.pitch_mm * (spec.footprint.pins_per_side - 1)
        actual_length = spec.footprint.body_length_mm
        if abs(expected_length - actual_length) > 0.5:
            report.errors.append(
                f"Geometric inconsistency: "
                f"pitch({spec.footprint.pitch_mm}mm) × (pins_per_side({spec.footprint.pins_per_side}) - 1) = "
                f"{expected_length:.2f}mm, but body_length is {actual_length:.2f}mm "
                f"(difference: {abs(expected_length - actual_length):.2f}mm, tolerance: ±0.5mm)"
            )

    # Rule 2: Pitch minimum
    if spec.footprint.pitch_mm is not None and spec.footprint.pitch_mm < 0.2:
        report.errors.append(f"Invalid pitch: {spec.footprint.pitch_mm}mm < 0.2mm minimum")

    # Rule 3: Pad width constraint (check per-pad widths if pads list exists)
    if spec.footprint.pitch_mm is not None:
        for pad in spec.footprint.pads:
            if pad.width_mm is not None and pad.width_mm > spec.footprint.pitch_mm:
                report.errors.append(
                    f"Invalid pad width: pad {pad.number} width {pad.width_mm}mm > pitch {spec.footprint.pitch_mm}mm"
                )

    # Rule 4: Pin count consistency
    if spec.footprint.pin_count != len(spec.symbol.pins):
        report.errors.append(
            f"Pin count mismatch: footprint has {spec.footprint.pin_count} pins, "
            f"but symbol has {len(spec.symbol.pins)} pins"
        )

    # Rule 5: Confidence check
    if spec.metadata.extraction_confidence < 0.8:
        report.warnings.append(
            f"Low extraction confidence: {spec.metadata.extraction_confidence:.1%} "
            f"(0.8+ recommended)"
        )

    # Rule 6: Unit heuristics for mil/inch detection
    # Suspected mils (values like 10-250 that would be tiny in mm)
    if (spec.footprint.pitch_mm is not None and
        spec.footprint.body_length_mm is not None and
        10 <= spec.footprint.pitch_mm <= 250 and
        spec.footprint.pitch_mm > spec.footprint.body_length_mm):
        report.warnings.append(
            f"Suspected mil values: pitch {spec.footprint.pitch_mm}mm seems unusually large; "
            f"did you mean {spec.footprint.pitch_mm * 0.0254:.3f}mm?"
        )

    # Obvious inch values (very large, like 0.5-1.0 inches)
    if spec.footprint.pitch_mm is not None and spec.footprint.pitch_mm > 10:
        report.warnings.append(
            f"Possible inch values: pitch {spec.footprint.pitch_mm}mm may be in inches; "
            f"converted to mm: {spec.footprint.pitch_mm * 25.4:.2f}mm"
        )

    return report
