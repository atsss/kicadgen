# generators

KiCAD file format generators for footprints and symbols.

## Module Overview

### `__init__.py`
Package initialization for generators subpackage.

### `footprint.py`
Generates KiCAD footprint (`.kicad_mod`) S-expression files for QFN packages.

**Functions:**
- `generate_footprint_sexpr(spec, part_number)`: Creates a complete .kicad_mod S-expression string

**Features:**
- QFN pad placement with edge pads and thermal pad
- Pad positioning calculated from pitch, body dimensions, and overlap
- S-expression format compatible with KiCAD 6+
- Includes reference and value text fields
- Supports layers: F.Cu, F.Paste, F.Mask, F.SilkS

**Pad Arrangement:**
- Bottom edge: pins 1 to pins_per_side
- Right edge: pins_per_side+1 to 2×pins_per_side
- Top edge: 2×pins_per_side+1 to 3×pins_per_side
- Left edge: 3×pins_per_side+1 to 4×pins_per_side
- Center thermal pad (approximately 70% of body width)

### `symbol.py`
Generates KiCAD symbol (`.kicad_sym`) S-expression files.

**Functions:**
- `generate_symbol_sexpr(spec, part_number)`: Creates a complete .kicad_sym S-expression string

**Features:**
- Pin distribution on left and right sides
- Configurable reference designator (default: U)
- S-expression format compatible with KiCAD 6+
- Supports property definitions (Reference, Value)
- Includes pin names, numbers, and types

**Pin Arrangement:**
- Left side: first half of pins
- Right side: second half of pins
- Vertical spacing distributed equally across symbol height

## Future Extensions

- Support for additional package types (QFP, SOIC, DIP, BGA)
- IPC-7351 compliance options
- 3D STEP file generation
- Thermal via support
