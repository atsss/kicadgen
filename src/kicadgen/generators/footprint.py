"""KiCAD footprint generation for QFN packages."""

from kicadgen.schema import FootprintSpec


def generate_footprint_sexpr(spec: FootprintSpec, part_number: str) -> str:
    """
    Generate a .kicad_mod S-expression string for a QFN footprint.

    Args:
        spec: FootprintSpec containing dimensions and pad information
        part_number: Component part number for labeling

    Returns:
        Valid .kicad_mod S-expression string
    """
    # QFN pad placement calculations
    pitch = spec.pitch_mm
    pins_per_side = spec.pins_per_side
    body_width = spec.body_width_mm
    body_length = spec.body_length_mm
    pad_width = spec.pad_width_mm
    pad_length = spec.pad_length_mm

    # Calculate pad positions
    pad_center_distance = body_length / 2 + pad_length / 2

    # Start building S-expression
    lines = [
        "(footprint \"{}\"".format(part_number),
        "  (version 6)",
        "  (generator \"kicadgen\")",
        "  (layer \"F.Cu\")",
        "  (attr smd)",
        "",
    ]

    # Add pads
    pad_count = 0

    # Bottom pads (pins 1 to pins_per_side)
    for i in range(pins_per_side):
        pad_num = i + 1
        x = -pitch * (pins_per_side - 1) / 2 + i * pitch
        y = body_length / 2 + pad_length / 2
        lines.append(
            "  (pad \"{}\" smd rect (at {:.3f} {:.3f}) (size {:.3f} {:.3f}) (layers \"F.Cu\" \"F.Paste\" \"F.Mask\"))".format(
                pad_num, x, y, pad_width, pad_length
            )
        )
        pad_count += 1

    # Right pads
    for i in range(pins_per_side):
        pad_num = pins_per_side + i + 1
        x = body_width / 2 + pad_length / 2
        y = pitch * (pins_per_side - 1) / 2 - i * pitch
        lines.append(
            "  (pad \"{}\" smd rect (at {:.3f} {:.3f}) (size {:.3f} {:.3f}) (layers \"F.Cu\" \"F.Paste\" \"F.Mask\") (rotate 90))".format(
                pad_num, x, y, pad_width, pad_length
            )
        )
        pad_count += 1

    # Top pads
    for i in range(pins_per_side):
        pad_num = pins_per_side * 2 + i + 1
        x = pitch * (pins_per_side - 1) / 2 - i * pitch
        y = -(body_length / 2 + pad_length / 2)
        lines.append(
            "  (pad \"{}\" smd rect (at {:.3f} {:.3f}) (size {:.3f} {:.3f}) (layers \"F.Cu\" \"F.Paste\" \"F.Mask\"))".format(
                pad_num, x, y, pad_width, pad_length
            )
        )
        pad_count += 1

    # Left pads
    for i in range(pins_per_side):
        pad_num = pins_per_side * 3 + i + 1
        x = -(body_width / 2 + pad_length / 2)
        y = -(pitch * (pins_per_side - 1) / 2 - i * pitch)
        lines.append(
            "  (pad \"{}\" smd rect (at {:.3f} {:.3f}) (size {:.3f} {:.3f}) (layers \"F.Cu\" \"F.Paste\" \"F.Mask\") (rotate 90))".format(
                pad_num, x, y, pad_width, pad_length
            )
        )
        pad_count += 1

    # Add thermal pad (central pad)
    thermal_size = body_width * 0.7
    lines.append(
        "  (pad \"TP\" smd rect (at 0 0) (size {:.3f} {:.3f}) (layers \"F.Cu\"))".format(
            thermal_size, thermal_size
        )
    )

    # Add reference and value text fields
    lines.extend(
        [
            "",
            "  (fp_text reference \"{}\" (at 0 {:.3f}) (layer \"F.SilkS\"))".format(
                "U?", -(body_length / 2 + 1.0)
            ),
            "    (effects (font (size 1.0 1.0) (thickness 0.15)))",
            "  )",
            "",
            "  (fp_text value \"{}\" (at 0 {:.3f}) (layer \"F.Fab\"))".format(
                part_number, body_length / 2 + 1.0
            ),
            "    (effects (font (size 1.0 1.0) (thickness 0.15)))",
            "  )",
            ")",
        ]
    )

    return "\n".join(lines)
