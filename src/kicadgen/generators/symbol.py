"""KiCAD symbol generation."""

from kicadgen.schema import SymbolSpec


def generate_symbol_sexpr(spec: SymbolSpec, part_number: str) -> str:
    """
    Generate a .kicad_sym S-expression string for a component symbol.

    Uses pin.side field when set; falls back to left/right split when not.

    Args:
        spec: SymbolSpec containing pin information
        part_number: Component part number for labeling

    Returns:
        Valid .kicad_sym S-expression string
    """
    lines = [
        '(kicad_symbol_lib (version 20211014) (generator "kicadgen")',
        '  (symbol "{}"'.format(part_number),
        "    (pin_numbers hide)",
        '    (property "Reference" "{}" (id 0) (at 0 0 0))'.format(
            spec.reference_prefix
        ),
        '    (property "Value" "{}" (id 1) (at 0 0 0))'.format(part_number),
        "",
    ]

    # Determine pin placement
    left_pins = []
    right_pins = []
    top_pins = []
    bottom_pins = []

    # Sort pins by explicit side or default to split
    has_explicit_sides = any(pin.side is not None for pin in spec.pins)

    if has_explicit_sides:
        for pin in spec.pins:
            if pin.side == "left":
                left_pins.append(pin)
            elif pin.side == "right":
                right_pins.append(pin)
            elif pin.side == "top":
                top_pins.append(pin)
            elif pin.side == "bottom":
                bottom_pins.append(pin)
            else:
                # Default to left if side is invalid
                left_pins.append(pin)
    else:
        # Default: split left and right
        pin_count = len(spec.pins)
        split_idx = pin_count // 2
        left_pins = spec.pins[:split_idx]
        right_pins = spec.pins[split_idx:]

    # Body dimensions (arbitrary, but consistent)
    pin_count = len(spec.pins)
    body_height = max(20, pin_count)
    body_width = 10

    # Add symbol drawing
    lines.extend(
        [
            '    (symbol "{}_1_1"'.format(part_number),
            "      (rectangle (start {:.1f} {:.1f}) (end {:.1f} {:.1f})".format(
                -body_width / 2, body_height / 2, body_width / 2, -body_height / 2
            ),
            "        (stroke (width 0.254) (type default))",
            "        (fill (type background))",
            "      )",
        ]
    )

    # Add left side pins
    if left_pins:
        for i, pin in enumerate(left_pins):
            y = (body_height / 2) - (i + 1) * (body_height / (len(left_pins) + 1))
            lines.append(
                '      (pin passive line (at {:.1f} {:.1f} 0) (length 2.54) (name "{}" (effects (font (size 1.27 1.27) (thickness 0.15)))) (number "{}" (effects (font (size 1.27 1.27) (thickness 0.15)))))'.format(
                    -body_width / 2 - 2.54, y, pin.name, pin.number
                )
            )

    # Add right side pins
    if right_pins:
        for i, pin in enumerate(right_pins):
            y = (body_height / 2) - (i + 1) * (body_height / (len(right_pins) + 1))
            lines.append(
                '      (pin passive line (at {:.1f} {:.1f} 180) (length 2.54) (name "{}" (effects (font (size 1.27 1.27) (thickness 0.15)))) (number "{}" (effects (font (size 1.27 1.27) (thickness 0.15)))))'.format(
                    body_width / 2 + 2.54, y, pin.name, pin.number
                )
            )

    # Add top side pins (if any)
    if top_pins:
        for i, pin in enumerate(top_pins):
            x = (-body_width / 2) + (i + 1) * (body_width / (len(top_pins) + 1))
            lines.append(
                '      (pin passive line (at {:.1f} {:.1f} 270) (length 2.54) (name "{}" (effects (font (size 1.27 1.27) (thickness 0.15)))) (number "{}" (effects (font (size 1.27 1.27) (thickness 0.15)))))'.format(
                    x, body_height / 2 + 2.54, pin.name, pin.number
                )
            )

    # Add bottom side pins (if any)
    if bottom_pins:
        for i, pin in enumerate(bottom_pins):
            x = (-body_width / 2) + (i + 1) * (body_width / (len(bottom_pins) + 1))
            lines.append(
                '      (pin passive line (at {:.1f} {:.1f} 90) (length 2.54) (name "{}" (effects (font (size 1.27 1.27) (thickness 0.15)))) (number "{}" (effects (font (size 1.27 1.27) (thickness 0.15)))))'.format(
                    x, -(body_height / 2 + 2.54), pin.name, pin.number
                )
            )

    lines.extend(
        [
            "    )",
            "  )",
            ")",
        ]
    )

    return "\n".join(lines)
