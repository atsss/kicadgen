# kicadgen Package

Core modules for PDF-to-KiCAD component specification extraction.

## Module Overview

### `__init__.py`
Package initialization. Exposes the kicadgen version.

### `cli.py`
Command-line interface using argparse. Entry point for the `kicadgen` command.

**Arguments:**
- `input_pdf` (positional): Path to component datasheet PDF
- `--part-number` (required): Component part number
- `--model` (optional, default: gpt-4o): VLM model (gpt-4o, claude-3-5-sonnet, gemini-1-5-pro)
- `--out` (optional, default: ./out): Output directory
- `--verbose` (flag): Enable debug logging
- `--dry-run` (flag): Skip file writing, only show validation report

### `schema.py`
Pydantic v2 data models representing component specifications.

**Classes:**
- `PinSpec`: Single pin specification (number, name, type)
- `MetaSpec`: Component metadata (part_number, package_type, confidence)
- `FootprintSpec`: Footprint dimensions and pad layout
- `SymbolSpec`: Symbol pin definitions
- `ComponentSpec`: Complete component specification (meta + footprint + symbol)

### `validator.py`
Validates extracted component specifications without raising exceptions.

**Classes:**
- `ValidationReport`: Contains errors and warnings lists

**Functions:**
- `validate_component(spec)`: Checks geometric consistency, pin counts, units, and constraints

**Validation Rules:**
1. Geometric: `pitch × (pins_per_side - 1) ≈ body_length` (±0.5mm tolerance)
2. Pitch minimum: 0.2mm
3. Pad width constraint: must not exceed pitch
4. Pin count: footprint and symbol must match
5. Unit heuristics: warns on suspected mil or inch values

### `pdf_processor.py`
PDF handling using PyMuPDF for page selection and image rendering.

**Functions:**
- `select_relevant_pages(doc, keywords)`: Scores and selects pages containing keywords
- `render_pages_to_png(doc, page_indices, dpi)`: Converts PDF pages to PNG bytes at specified DPI

### `vlm_client.py`
Abstract VLM client interface with three concrete implementations.

**Classes:**
- `VLMClient` (ABC): Abstract base class
- `OpenAIClient`: GPT-4o via OpenAI API
- `AnthropicClient`: Claude 3.5 Sonnet via Anthropic API
- `GeminiClient`: Gemini 1.5 Pro via Google API

**Functions:**
- `get_client(model)`: Factory function to instantiate the correct client

**Environment Variables:**
- `OPENAI_API_KEY`: For OpenAI
- `ANTHROPIC_API_KEY`: For Anthropic
- `GEMINI_API_KEY`: For Google Gemini

### `extractor.py`
VLM-based extraction of component specifications from datasheet images.

**Classes:**
- `ExtractionError`: Raised when extraction fails after max retries

**Functions:**
- `build_prompt(part_number)`: Constructs the VLM extraction prompt
- `parse_json_from_response(text)`: Parses JSON from VLM response (handles markdown)
- `extract(client, images, part_number, max_retries)`: Orchestrates extraction with retry logic

### `pipeline.py`
Orchestrates the complete workflow from PDF to KiCAD files.

**Functions:**
- `write_validation_report(report, path)`: Writes validation results to text file
- `run(args)`: Main pipeline orchestration

**Pipeline Steps:**
1. Load PDF
2. Select relevant pages
3. Render pages to PNG
4. Call VLM for extraction
5. Validate specification
6. Generate KiCAD files (if validation passes)
7. Write outputs

### `generators/` (subdirectory)
Contains KiCAD format generators.

### `utils/` (subdirectory)
Contains utility modules for logging and temporary file management.
