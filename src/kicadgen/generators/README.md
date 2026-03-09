# generators

KiCAD file format generators for footprints and symbols.

## Module Overview

### `__init__.py`
Package initialization for generators subpackage.

### `footprint.py`
Generates KiCAD footprint (`.kicad_mod`) S-expression files.

**Functions:**
- `generate_footprint_sexpr(spec, part_number)`: Creates a complete .kicad_mod S-expression string

**Features:**
- **Explicit pad mode**: Uses `pads[].{x_mm, y_mm, width_mm, length_mm, shape}` when provided
- **Computed QFN layout**: Falls back to calculated QFN arrangement when pads list is empty
  - Bottom edge: pins 1 to pins_per_side
  - Right edge: pins_per_side+1 to 2×pins_per_side
  - Top edge: 2×pins_per_side+1 to 3×pins_per_side
  - Left edge: 3×pins_per_side+1 to 4×pins_per_side
  - Center thermal pad (approximately 70% of body width)
- S-expression format compatible with KiCAD 6+
- Supports pad types: smd, through_hole
- Includes reference and value text fields
- Supports layers: F.Cu, F.Paste, F.Mask, F.SilkS

### `symbol.py`
Generates KiCAD symbol (`.kicad_sym`) S-expression files.

**Functions:**
- `generate_symbol_sexpr(spec, part_number)`: Creates a complete .kicad_sym S-expression string

**Features:**
- **Explicit pin placement**: Uses `pin.side` field (left, right, top, bottom) when set
- **Fallback distribution**: Splits pins left/right automatically when side is not set
- Reference designator from `symbol.reference_prefix`
- S-expression format compatible with KiCAD 6+
- Supports property definitions (Reference, Value)
- Includes pin names, numbers, types, and unit indices

**Pin Arrangement:**
- Left side: pins with side="left" or first half if no sides specified
- Right side: pins with side="right" or second half if no sides specified
- Top side: pins with side="top" (if specified)
- Bottom side: pins with side="bottom" (if specified)
- Vertical/horizontal spacing distributed equally

## Future Extensions

- Support for additional package types (QFP, SOIC, DIP, BGA)
- IPC-7351 compliance options
- 3D STEP file generation
- Thermal via support
