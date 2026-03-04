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

# 6. Intermediate JSON Schema

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

# 7. Validation Rules

## 7.1 Geometric Consistency

```
pitch_mm × (pins_per_side - 1)
≈ body_length_mm (tolerance ±0.5mm)
```

## 7.2 Abnormal Value Detection

| Condition | Error |
|------------|--------|
| pitch_mm < 0.2 | Invalid |
| pad_width_mm > pitch_mm | Invalid |
| pin_count != number of symbol pins | Error |

## 7.3 Unit Validation

- Suspected mil values must trigger a warning
- Obvious inch values require conversion request

---

# 8. KiCAD Generation

## 8.1 Target Format

KiCAD 6+ S-expression format:

- `.kicad_mod`
- `.kicad_sym`

---

## 8.2 Initially Supported Package Types

- QFN
- QFP
- SOIC
- DIP

---

## 8.3 Pad Placement Rules

- Origin at package center
- Pin 1 located at top-left (default orientation)
- IPC-7351 compliance option (future extension)

---

# 9. Output Structure

```
out/
 ├── <part>.kicad_mod
 ├── <part>.kicad_sym
 ├── extracted.json
 └── validation_report.txt
```

---

# 10. Error Handling

| Situation | Behavior |
|------------|------------|
| Invalid JSON | Retry extraction |
| confidence < 0.8 | Warning |
| Validation failure | Abort KiCAD generation |
| API failure | Retry up to 3 times |

---

# 11. Security Requirements

- API keys must be provided via environment variables
- API keys must never appear in logs
- PDF data must not be externally stored
- Temporary images must be deleted after processing

---

# 12. Non-Functional Requirements

| Item | Requirement |
|------|-------------|
| OS | Linux / macOS |
| Execution Mode | CLI |
| Public Exposure | Not allowed |
| Local Storage | Allowed |
| Parallel Processing | Future support |

---

# 13. Development Phases

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

# 14. Limitations

- Highly dependent on datasheet format
- Sensitive to manufacturer formatting variations
- Special packages not supported initially
- 3D STEP generation not supported

---

# 15. Design Philosophy

This tool does not aim for full automation.

Core philosophy:

AI extraction + engineering validation = practical reliability
