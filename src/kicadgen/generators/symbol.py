"""KiCAD symbol generation."""

from kicadgen.schema import SymbolSpec


def generate_symbol_sexpr(spec: SymbolSpec, part_number: str) -> str:
    """
    Generate a .kicad_sym S-expression string for a component symbol.

    Args:
        spec: SymbolSpec containing pin information
        part_number: Component part number for labeling

    Returns:
        Valid .kicad_sym S-expression string
    """
    lines = [
        "(symbol \"{}\"".format(part_number),
        "  (pin_numbers hide)",
        "  (property \"Reference\" \"{}\" (id 0) (at 0 0 0))".format(spec.reference),
        "  (property \"Value\" \"{}\" (id 1) (at 0 0 0))".format(part_number),
        "",
    ]

    # Calculate pin positions (distribute on left and right)
    pin_count = len(spec.pins)
    left_pins = pin_count // 2
    right_pins = pin_count - left_pins

    # Body dimensions (arbitrary, but consistent)
    body_height = max(20, pin_count)
    body_width = 10
    x_offset = -body_width / 2
    y_offset = body_height / 2

    # Add symbol drawing
    lines.extend(
        [
            "  (symbol \"{}_1_1\"".format(part_number),
            "    (rectangle (start {:.1f} {:.1f}) (end {:.1f} {:.1f})".format(
                -body_width / 2, body_height / 2, body_width / 2, -body_height / 2
            ),
            "      (stroke (width 0.254) (type default))",
            "      (fill (type background))",
            "    )",
        ]
    )

    # Add pins
    for i, pin in enumerate(spec.pins):
        if i < left_pins:
            # Left side pins
            y = y_offset - (i * body_height / max(left_pins, 1))
            lines.append(
                "    (pin passive line (at {:.1f} {:.1f} 0) (length 2.54) (name \"{}\" (effects (font (size 1.27 1.27) (thickness 0.15)))) (number \"{}\" (effects (font (size 1.27 1.27) (thickness 0.15)))))".format(
                    -body_width / 2 - 2.54, y, pin.name, pin.number
                )
            )
        else:
            # Right side pins
            pin_idx = i - left_pins
            y = y_offset - (pin_idx * body_height / max(right_pins, 1))
            lines.append(
                "    (pin passive line (at {:.1f} {:.1f} 180) (length 2.54) (name \"{}\" (effects (font (size 1.27 1.27) (thickness 0.15)))) (number \"{}\" (effects (font (size 1.27 1.27) (thickness 0.15)))))".format(
                    body_width / 2 + 2.54, y, pin.name, pin.number
                )
            )

    lines.extend(
        [
            "  )",
            ")",
        ]
    )

    return "\n".join(lines)
