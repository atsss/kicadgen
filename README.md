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

- KiCAD 6+ format files:
  - `.kicad_mod`
  - `.kicad_sym`
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
- `confidence` field is mandatory

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
- `PinSpec(number, name, type)`
- `MetaSpec(part_number, package_type, confidence)`
- `FootprintSpec(pin_count, pins_per_side, pitch_mm, pad_width_mm, pad_length_mm, body_width_mm, body_length_mm, pin1_location)`
- `SymbolSpec(reference="U", pins: list[PinSpec])`
- `ComponentSpec(meta, footprint, symbol)`

### validator.py
Depends on: `schema.py`

Validates extracted data:
- Geometric consistency: `pitch_mm × (pins_per_side - 1) ≈ body_length_mm` (±0.5mm tolerance)
- Pitch minimum: `pitch_mm >= 0.2mm`
- Pad constraint: `pad_width_mm <= pitch_mm`
- Pin count match: `pin_count == len(symbol.pins)`
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
- QFN pad placement (edge pads + thermal pad)
- Pad centers calculated from pitch, body dimensions, and overlap
- Valid KiCAD 6+ format output

### generators/symbol.py
Depends on: `schema.py`

Generates `.kicad_sym` S-expression:
- Pin distribution on left/right sides
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
5. Validate results
6. Generate KiCAD files (if valid)
7. Write outputs and reports

### cli.py
Depends on: `pipeline.py`

argparse-based CLI with arguments:
- `input_pdf` (positional, required)
- `--part-number` (required)
- `--model` (default: `gpt-4o`)
- `--out` (default: `./out`)
- `--verbose` (flag)
- `--dry-run` (flag)

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

# 7. Intermediate JSON Schema

## 6.1 Root Schema

```json
{
  "meta": {
    "part_number": "",
    "package_type": "",
    "confidence": 0.0
  },
  "footprint": {
    "pin_count": 0,
    "pins_per_side": 0,
    "pitch_mm": 0.0,
    "pad_width_mm": 0.0,
    "pad_length_mm": 0.0,
    "body_width_mm": 0.0,
    "body_length_mm": 0.0,
    "pin1_location": ""
  },
  "symbol": {
    "reference": "U",
    "pins": [
      {
        "number": "",
        "name": "",
        "type": ""
      }
    ]
  }
}
```

---

# 8. Validation Rules

## 8.1 Geometric Consistency

```
pitch_mm × (pins_per_side - 1)
≈ body_length_mm (tolerance ±0.5mm)
```

## 8.2 Abnormal Value Detection

| Condition | Error |
|------------|--------|
| pitch_mm < 0.2 | Invalid |
| pad_width_mm > pitch_mm | Invalid |
| pin_count != number of symbol pins | Error |

## 8.3 Unit Validation

- Suspected mil values must trigger a warning
- Obvious inch values require conversion request

---

# 9. KiCAD Generation

## 9.1 Target Format

KiCAD 6+ S-expression format:

- `.kicad_mod`
- `.kicad_sym`

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
 ├── <part>.kicad_mod
 ├── <part>.kicad_sym
 ├── extracted.json
 └── validation_report.txt
```

---

# 11. Error Handling

| Situation | Behavior |
|------------|------------|
| Invalid JSON | Retry extraction |
| confidence < 0.8 | Warning |
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

- PDF → AI extraction
- JSON output
- QFN-only generation

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
