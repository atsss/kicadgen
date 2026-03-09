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
- `--no-review` (flag): Skip human review of extracted JSON before validation (for automated/CI runs)

### `schema.py`
Pydantic v2 data models representing normalized component specifications.

**Classes:**
- `PadSpec`: Single pad with explicit coordinates (number, x_mm, y_mm, width_mm, length_mm, drill_mm, shape)
- `ComponentInfo`: Component metadata (name, manufacturer, part_number, description, package_type, datasheet_source)
- `MetadataSpec`: AI extraction metadata (extraction_confidence, missing_fields, assumptions, source_pages)
- `PinSpec`: Pin with type and placement hints (number, name, type, side, unit)
- `FootprintSpec`: Footprint with pad coordinates (pin_count, pins_per_side, pad_type, pad_shape, pitch_mm, pads, body dimensions)
- `SymbolSpec`: Symbol specification (pin_count, pin_pitch_grid, reference_prefix, pins)
- `ComponentSpec`: Complete normalized specification (component, symbol, footprint, metadata)

### `validator.py`
Validates extracted component specifications without raising exceptions.

**Classes:**
- `ValidationReport`: Contains errors and warnings lists

**Functions:**
- `validate_component(spec)`: Checks geometric consistency, pin counts, confidence, and constraints

**Validation Rules:**
1. Geometric: `pitch × (pins_per_side - 1) ≈ body_length` (±0.5mm tolerance, when provided)
2. Pitch minimum: 0.2mm (when provided)
3. Pad width constraint: per-pad width must not exceed pitch
4. Pin count: footprint.pin_count must match len(symbol.pins)
5. Confidence check: warns if extraction_confidence < 0.8
6. Unit heuristics: warns on suspected mil or inch values

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
VLM-based extraction of normalized component specifications from datasheet images.

**Classes:**
- `ExtractionError`: Raised when extraction fails after max retries

**Functions:**
- `build_prompt(part_number)`: Constructs the VLM extraction prompt with normalized JSON schema
- `parse_json_from_response(text)`: Parses JSON from VLM response (handles markdown fences)
- `extract(client, images, part_number, max_retries)`: Orchestrates extraction with retry logic, returns ComponentSpec

**Output Schema:** Matches the normalized schema from `schema.py` with component, symbol, footprint, and metadata sections

### `pipeline.py`
Orchestrates the complete workflow from PDF to KiCAD files.

**Functions:**
- `prompt_human_review(spec, extracted_path)`: Displays summary of extracted specification and waits for user confirmation before validation. Shows component info, confidence, footprint details, missing fields, and assumptions. Returns `True` to proceed, `False` to abort.
- `write_validation_report(report, path)`: Writes validation results to text file
- `run(args)`: Main pipeline orchestration

**Pipeline Steps:**
1. Load PDF
2. Select relevant pages
3. Render pages to PNG
4. Call VLM for extraction
5. Save extracted.json
6. **[Human Review]** — prompt user to review extracted data (unless `--no-review` flag)
7. Validate specification
8. Generate KiCAD files (if validation passes)
9. Write outputs and validation report

**User Interactions:**
- Review prompt accepts: `y`/Enter to proceed, `n`/`q` to abort (exit code 1)
- User can manually edit extracted.json while prompt waits
- Invalid input loops until valid response given

### `generators/` (subdirectory)
Contains KiCAD format generators.

### `utils/` (subdirectory)
Contains utility modules for logging and temporary file management.
