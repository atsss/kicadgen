"""KiCAD footprint generation for packages."""

from kicadgen.schema import FootprintSpec


def generate_footprint_sexpr(spec: FootprintSpec, part_number: str) -> str:
    """
    Generate a .kicad_mod S-expression string for a footprint.

    Supports two modes:
    1. Explicit pad coordinates: Uses pads[].{x_mm, y_mm, width_mm, length_mm, shape}
    2. Computed QFN layout: Falls back to QFN layout if pads list is empty

    Args:
        spec: FootprintSpec containing dimensions and pad information
        part_number: Component part number for labeling

    Returns:
        Valid .kicad_mod S-expression string
    """
    # Normalize human-readable shape names to KiCAD tokens
    SHAPE_MAP = {
        "rectangle": "rect",
        "rectangular": "rect",
        "rect": "rect",
        "oval": "oval",
        "circle": "circle",
        "circular": "circle",
        "roundrect": "roundrect",
        "round_rect": "roundrect",
        "trapezoid": "trapezoid",
        "custom": "custom",
    }

    # Start building S-expression
    lines = [
        '(footprint "{}"'.format(part_number),
        "  (version 20241229)",
        '  (generator "kicadgen")',
        '  (layer "F.Cu")',
        "  (attr smd)",
        "",
    ]

    # If explicit pads are provided, use them
    if spec.pads:
        for pad in spec.pads:
            pad_width = pad.width_mm if pad.width_mm is not None else 0.5
            pad_length = pad.length_mm if pad.length_mm is not None else 1.0
            raw_shape = (pad.shape or "rect").lower().strip()
            pad_shape = SHAPE_MAP.get(raw_shape, raw_shape)

            lines.append(
                '  (pad "{}" smd {} (at {:.3f} {:.3f}) (size {:.3f} {:.3f}) (layers "F.Cu" "F.Paste" "F.Mask"))'.format(
                    pad.number, pad_shape, pad.x_mm, pad.y_mm, pad_width, pad_length
                )
            )
    else:
        # Fallback to computed QFN layout
        if (
            spec.pitch_mm is not None
            and spec.pins_per_side is not None
            and spec.body_length_mm is not None
            and spec.body_width_mm is not None
        ):
            pitch = spec.pitch_mm
            pins_per_side = spec.pins_per_side
            body_width = spec.body_width_mm
            body_length = spec.body_length_mm
            # Default pad dimensions if not provided
            pad_width = 0.3
            pad_length = 0.8

            # Bottom pads (pins 1 to pins_per_side)
            for i in range(pins_per_side):
                pad_num = i + 1
                x = -pitch * (pins_per_side - 1) / 2 + i * pitch
                y = body_length / 2 + pad_length / 2
                lines.append(
                    '  (pad "{}" smd rect (at {:.3f} {:.3f}) (size {:.3f} {:.3f}) (layers "F.Cu" "F.Paste" "F.Mask"))'.format(
                        pad_num, x, y, pad_width, pad_length
                    )
                )

            # Right pads
            for i in range(pins_per_side):
                pad_num = pins_per_side + i + 1
                x = body_width / 2 + pad_length / 2
                y = pitch * (pins_per_side - 1) / 2 - i * pitch
                lines.append(
                    '  (pad "{}" smd rect (at {:.3f} {:.3f}) (size {:.3f} {:.3f}) (layers "F.Cu" "F.Paste" "F.Mask") (rotate 90))'.format(
                        pad_num, x, y, pad_width, pad_length
                    )
                )

            # Top pads
            for i in range(pins_per_side):
                pad_num = pins_per_side * 2 + i + 1
                x = pitch * (pins_per_side - 1) / 2 - i * pitch
                y = -(body_length / 2 + pad_length / 2)
                lines.append(
                    '  (pad "{}" smd rect (at {:.3f} {:.3f}) (size {:.3f} {:.3f}) (layers "F.Cu" "F.Paste" "F.Mask"))'.format(
                        pad_num, x, y, pad_width, pad_length
                    )
                )

            # Left pads
            for i in range(pins_per_side):
                pad_num = pins_per_side * 3 + i + 1
                x = -(body_width / 2 + pad_length / 2)
                y = -(pitch * (pins_per_side - 1) / 2 - i * pitch)
                lines.append(
                    '  (pad "{}" smd rect (at {:.3f} {:.3f}) (size {:.3f} {:.3f}) (layers "F.Cu" "F.Paste" "F.Mask") (rotate 90))'.format(
                        pad_num, x, y, pad_width, pad_length
                    )
                )

            # Add thermal pad (central pad) if body dimensions allow
            thermal_size = body_width * 0.7
            lines.append(
                '  (pad "TP" smd rect (at 0 0) (size {:.3f} {:.3f}) (layers "F.Cu"))'.format(
                    thermal_size, thermal_size
                )
            )

            # Add reference and value text fields
            lines.extend(
                [
                    "",
                    '  (fp_text reference "{}" (at 0 {:.3f}) (layer "F.SilkS")'.format(
                        "U?", -(body_length / 2 + 1.0)
                    ),
                    "    (effects (font (size 1.0 1.0) (thickness 0.15)))",
                    "  )",
                    "",
                    '  (fp_text value "{}" (at 0 {:.3f}) (layer "F.Fab")'.format(
                        part_number, body_length / 2 + 1.0
                    ),
                    "    (effects (font (size 1.0 1.0) (thickness 0.15)))",
                    "  )",
                ]
            )

    # Close footprint if no computed layout was added
    if not spec.pads or (spec.pitch_mm is None or spec.pins_per_side is None):
        # Only add text fields if they weren't already added by computed layout
        if not (
            spec.pitch_mm is not None
            and spec.pins_per_side is not None
            and spec.body_length_mm is not None
            and spec.body_width_mm is not None
        ):
            lines.extend(
                [
                    "",
                    '  (fp_text reference "{}" (at 0 -3.0) (layer "F.SilkS")'.format(
                        "U?"
                    ),
                    "    (effects (font (size 1.0 1.0) (thickness 0.15)))",
                    "  )",
                    "",
                    '  (fp_text value "{}" (at 0 3.0) (layer "F.Fab")'.format(
                        part_number
                    ),
                    "    (effects (font (size 1.0 1.0) (thickness 0.15)))",
                    "  )",
                ]
            )

    lines.append(")")

    return "\n".join(lines)
