# KiCAD Footprint & Symbol Generator
## CLI-Based AI-Assisted Specification Extraction Tool
**Version 0.1 (Draft Specification)**

---

# 1. Overview

This tool is a CLI application that generates KiCAD footprint (`.kicad_mod`) and symbol (`.kicad_sym`) files from electronic component datasheets (PDF).

The system runs locally but uses external LLM/VLM APIs for specification extraction.

The tool is not intended to be publicly exposed on the internet.

---

# 2. Scope

## 2.1 Input

- Electronic component datasheet (PDF format)
- Must include:
  - Mechanical drawing
  - Pin configuration table

## 2.2 Output

- KiCAD 9 format files:
  - `.kicad_mod`
  - `.kicad_sym`
  - `.zip` (archive combining `.kicad_mod` and `.kicad_sym`)
- Extracted structured JSON
- Validation report (text format)

---

# 3. System Architecture

```
CLI
 ↓
PDF Parsing (Local)
 ↓
Target Page Selection
 ↓
Image Conversion (PNG)
 ↓
VLM API Call
 ↓
Structured JSON Extraction
 ↓
[Human Review] ← pauses for user confirmation
 ↓
Validation
 ↓
KiCAD File Generation
 ↓
Output
```

---

# 4. External AI Services

## 4.1 Supported APIs

- OpenAI GPT-4o
- Anthropic Claude 3.5 Sonnet
- Google Gemini 1.5 Pro

Recommended: GPT-4o (high JSON formatting reliability)

---

# 5. Functional Requirements

## 5.1 CLI Interface

```bash
kicadgen <input.pdf> \
  --part-number <string> \
  --model <model_name> \
  --out <output_dir>
```

### Required Arguments

- `input.pdf`
- `--part-number`

### Optional Arguments

- `--model` (default: gpt-4o)
- `--out` (default: ./out)
- `--verbose`
- `--dry-run`
- `--no-review` (skip human review of extracted JSON)

---

## 5.2 PDF Processing

- Use PyMuPDF
- Render pages at ≥300 DPI
- Use OCR to detect relevant pages containing:
  - "Recommended Land Pattern"
  - "Package Dimensions"
  - "Pin Configuration"

---

## 5.3 AI Extraction Requirements

- Strict JSON output
- All units must be in millimeters (mm)
- No estimation or guessing allowed
- Missing values must be returned as null
- `extraction_confidence` field is mandatory (0.0-1.0)

---

## 5.4 Human Review Step

After AI extraction, before validation, the pipeline pauses for human review:

- Displays a summary of extracted fields (component info, confidence, footprint details)
- Shows path to `extracted.json` for manual inspection/editing
- Prompts user: "Proceed with validation? [Y/n]:"
- **Enabled by default** — use `--no-review` flag to skip (for automated/CI usage)
- User can:
  - Press **Enter** or type **`y`** → continue to validation
  - Type **`n`** or **`q`** → abort pipeline (exit code 1)

---

# 6. Implementation Plan

## 6.1 Project Structure

```
kicadgen/
├── pyproject.toml
├── .env.example
├── src/
│   └── kicadgen/
│       ├── __init__.py
│       ├── cli.py               # argparse entry point
│       ├── pipeline.py          # orchestration
│       ├── pdf_processor.py     # PyMuPDF page selection + PNG render
│       ├── vlm_client.py        # OpenAI / Anthropic / Gemini clients
│       ├── extractor.py         # VLM prompt + retry + JSON parse
│       ├── schema.py            # Pydantic v2 models
│       ├── validator.py         # geometric + unit validation
│       ├── generators/
│       │   ├── __init__.py
│       │   ├── footprint.py     # .kicad_mod S-expression (QFN)
│       │   └── symbol.py        # .kicad_sym S-expression
│       └── utils/
│           ├── __init__.py
│           ├── logging.py       # verbose/quiet logger
│           └── tempfiles.py     # TempImageDir context manager
└── tests/
    ├── test_validator.py
    ├── test_extractor.py
    ├── test_footprint.py
    ├── test_symbol.py
    └── fixtures/
        └── sample_extracted.json
```

## 6.2 Module Dependencies

### schema.py
Core Pydantic v2 models (foundational):
- `PadSpec(number, x_mm, y_mm, width_mm, length_mm, drill_mm, shape)` — explicit per-pad coordinates
- `ComponentInfo(name, manufacturer, part_number, description, package_type, datasheet_source)` — component metadata
- `MetadataSpec(extraction_confidence, missing_fields, assumptions, source_pages)` — AI extraction metadata
- `PinSpec(number, name, type, side, unit)` — pin with optional placement hints
- `SymbolSpec(pin_count, pin_pitch_grid=None, reference_prefix=None, pins: list[PinSpec])` — pin_pitch_grid defaults to 2.54mm, reference_prefix defaults to "U" if not extracted
- `FootprintSpec(pin_count, pins_per_side, pad_type, pad_shape, pitch_mm, pads, body_width_mm, body_length_mm, body_height_mm, pin1_location)`
- `ComponentSpec(component, symbol, footprint, metadata)` — complete specification

### validator.py
Depends on: `schema.py`

Validates extracted data:
- Geometric consistency: `pitch_mm × (pins_per_side - 1) ≈ body_length_mm` (±0.5mm tolerance, when both values provided)
- Pitch minimum: `pitch_mm >= 0.2mm`
- Pad constraint: per-pad `width_mm <= pitch_mm`
- Pin count match: `pin_count == len(symbol.pins)`
- Confidence check: `extraction_confidence < 0.8` triggers warning
- Unit heuristics for mil/inch detection

Returns `ValidationReport(errors: list[str], warnings: list[str])` without raising exceptions.

### pdf_processor.py
Depends on: PyMuPDF

Two functions:
- `select_relevant_pages(doc, keywords) -> list[int]`: Keyword-based page scoring
- `render_pages_to_png(doc, page_indices, dpi=300) -> list[bytes]`: Convert to PNG images

### vlm_client.py
Depends on: `openai`, `anthropic`, `google-generativeai`

Abstract base + three concrete implementations:
- `OpenAIClient`: Uses `OPENAI_API_KEY`, GPT-4o
- `AnthropicClient`: Uses `ANTHROPIC_API_KEY`, Claude 3.5 Sonnet
- `GeminiClient`: Uses `GEMINI_API_KEY`, Gemini 1.5 Pro
- `get_client(model: str) -> VLMClient`: Factory function

### extractor.py
Depends on: `schema.py`, `vlm_client.py`

Functions:
- `build_prompt(part_number) -> str`: Constructs VLM prompt with schema and context
- `parse_json_from_response(text) -> dict`: Extracts JSON from VLM response (handles markdown fences)
- `extract(client, images, part_number, max_retries=3) -> ComponentSpec`: Orchestrates extraction with retry logic

### generators/footprint.py
Depends on: `schema.py`

Generates `.kicad_mod` S-expression:
- **Explicit pad placement**: Uses `pads[].{x_mm, y_mm, width_mm, length_mm, shape}` when provided
- **Fallback computed layout**: QFN layout from `pitch_mm`, `pins_per_side`, body dimensions when `pads` is empty
- Pad type and shape from `pad_type` and `pad_shape` fields
- Valid KiCAD 6+ format output

### generators/symbol.py
Depends on: `schema.py`

Generates `.kicad_sym` S-expression:
- **Pin placement hints**: Uses `pin.side` field when set (`left`/`right`/`top`/`bottom`)
- **Fallback distribution**: Splits pins left/right when `side` is not set
- Reference designator from `symbol.reference_prefix`
- Valid KiCAD 6+ format output

### utils/tempfiles.py
Context manager for temporary image directories:
```python
class TempImageDir:
    def __enter__(self) -> Path: ...
    def __exit__(self, *_): ...
```

### utils/logging.py
Setup verbose/quiet logging based on CLI flags.

### pipeline.py
Depends on: all modules

Orchestrates the full workflow:
1. Load PDF
2. Select relevant pages
3. Render to PNG images
4. Call VLM extraction
5. Save extracted.json
6. **[Human Review]** — prompt user to review extracted data (unless --no-review)
7. Validate results
8. Generate KiCAD files (if valid)
9. Create zip archive of `.kicad_mod` and `.kicad_sym`
10. Write outputs and reports

**Key Functions:**
- `prompt_human_review(spec, extracted_path)`: Displays extraction summary and waits for user confirmation
- `write_validation_report(report, output_path)`: Writes validation results to file

### cli.py
Depends on: `pipeline.py`

argparse-based CLI with arguments:
- `input_pdf` (positional, required)
- `--part-number` (required)
- `--model` (default: `gpt-4o`)
- `--out` (default: `./out`)
- `--verbose` (flag)
- `--dry-run` (flag)
- `--no-review` (flag) — skip human review step before validation

## 6.3 Dependencies (pyproject.toml)

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "kicadgen"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "pymupdf>=1.24",
    "pydantic>=2.0",
    "openai>=1.30",
    "anthropic>=0.28",
    "google-generativeai>=0.7",
]

[project.optional-dependencies]
dev = ["pytest>=8.0", "pytest-cov", "ruff", "mypy"]

[project.scripts]
kicadgen = "kicadgen.cli:main"
```

## 6.4 Installation

```bash
uv pip install -e ".[dev]"
kicadgen --help
```

---

# 7. Normalized JSON Schema

## 7.1 Root Schema

The normalized JSON output follows this structure:

```json
{
  "component": {
    "name": "",
    "manufacturer": "",
    "part_number": "",
    "description": null,
    "package_type": "",
    "datasheet_source": null
  },
  "symbol": {
    "pin_count": 0,
    "pin_pitch_grid": 2.54,
    "reference_prefix": "U",
    "pins": [
      {
        "number": "",
        "name": "",
        "type": "",
        "side": null,
        "unit": 1
      }
    ]
  },
  "footprint": {
    "pin_count": 0,
    "pins_per_side": null,
    "pad_type": "smd",
    "pad_shape": "rectangle",
    "pitch_mm": null,
    "pads": [
      {
        "number": "",
        "x_mm": 0.0,
        "y_mm": 0.0,
        "width_mm": null,
        "length_mm": null,
        "drill_mm": null,
        "shape": ""
      }
    ],
    "body_width_mm": null,
    "body_length_mm": null,
    "body_height_mm": null,
    "pin1_location": null
  },
  "metadata": {
    "extraction_confidence": 0.0,
    "missing_fields": [],
    "assumptions": [],
    "source_pages": []
  }
}
```

## 7.2 Schema Field Descriptions

- **component**: General device information from datasheet
- **symbol**: Electrical schematic representation (pin layout, reference prefix)
- **footprint**: Physical PCB layout (pad positions, body dimensions, pad types)
- **metadata**: AI extraction confidence, missing fields, assumptions, source page numbers

Key design principles:
- All dimensions normalized to **millimeters (mm)**
- Missing values are `null`, never zero or guessed
- Pin numbering matches datasheet exactly
- Pad coordinates use package center as origin
- Per-pad explicit coordinates override computed layout

Optional fields with system defaults (can be null in extracted JSON):
- `component.description` — optional metadata, can be null
- `component.datasheet_source` — optional metadata, can be null
- `symbol.pin_pitch_grid` — system applies 2.54mm default if null
- `symbol.reference_prefix` — system applies "U" default if null

---

# 8. Validation Rules

## 8.1 Geometric Consistency

When `pins_per_side` and `pitch_mm` are provided:
```
pitch_mm × (pins_per_side - 1)
≈ body_length_mm (tolerance ±0.5mm)
```

## 8.2 Abnormal Value Detection

| Condition | Error |
|------------|--------|
| pitch_mm < 0.2 | Invalid |
| per-pad width_mm > pitch_mm | Invalid |
| pin_count != len(symbol.pins) | Error |
| extraction_confidence < 0.8 | Warning |

## 8.3 Unit Validation

- Suspected mil values must trigger a warning
- Obvious inch values require conversion request

## 8.4 Missing Field Handling

- Fields not found in datasheet are marked `null`
- Missing field names are listed in `metadata.missing_fields`
- Any inferred or assumed values are documented in `metadata.assumptions`

---

# 9. KiCAD Generation

## 9.1 Target Format

KiCAD 9 S-expression format:

- `.kicad_mod` (version 20241229)
- `.kicad_sym`

**Note:** This tool is designed for **KiCAD 9 only**. Generated files use the KiCAD 9 footprint format version (20241229) and may not be compatible with earlier KiCAD versions.

---

## 9.2 Initially Supported Package Types

- QFN
- QFP
- SOIC
- DIP

---

## 9.3 Pad Placement Rules

- Origin at package center
- Pin 1 located at top-left (default orientation)
- IPC-7351 compliance option (future extension)

---

# 10. Output Structure

```
out/
 └── <timestamp>/
     ├── <part>.kicad_mod
     ├── <part>.kicad_sym
     ├── <part>.zip          (archive of .kicad_mod and .kicad_sym)
     ├── extracted.json
     └── validation_report.txt
```

---

# 11. Error Handling

| Situation | Behavior |
|------------|------------|
| Invalid JSON | Retry extraction |
| metadata.extraction_confidence < 0.8 | Warning during review |
| User aborts during review | Exit code 1, no validation/generation |
| Validation failure | Abort KiCAD generation |
| API failure | Retry up to 3 times |

---

# 12. Security Requirements

- API keys must be provided via environment variables
- API keys must never appear in logs
- PDF data must not be externally stored
- Temporary images must be deleted after processing

---

# 13. Non-Functional Requirements

| Item | Requirement |
|------|-------------|
| OS | Linux / macOS |
| Execution Mode | CLI |
| Public Exposure | Not allowed |
| Local Storage | Allowed |
| Parallel Processing | Future support |

---

# 14. Development Phases

## Phase 1 (MVP)

- PDF → AI extraction with normalized JSON schema
- Human review step before validation
- JSON output with metadata (confidence, missing fields, assumptions)
- QFN-only generation
- Basic validation with unit heuristics

## Phase 2

- Enhanced validation
- Re-query logic for inconsistency resolution

## Phase 3

- IPC corrections
- JEDEC standard dimension reference
- Expanded package support

---

# 15. Limitations

- Highly dependent on datasheet format
- Sensitive to manufacturer formatting variations
- Special packages not supported initially
- 3D STEP generation not supported

---

# 16. Design Philosophy

This tool does not aim for full automation.

Core philosophy:

AI extraction + engineering validation = practical reliability
