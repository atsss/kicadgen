# tests

Unit test suite for kicadgen package.

## Running Tests

```bash
pytest tests/                    # Run all tests
pytest tests/ -v                 # Verbose output
pytest tests/ --cov              # With coverage report
pytest tests/test_validator.py   # Run specific test file
```

## Test Files Overview

### `__init__.py`
Package initialization for tests.

### `test_validator.py`
Tests for the validator module.

**Coverage:**
- Geometric consistency validation
- Pitch minimum constraint
- Pad width constraint
- Pin count matching
- Unit heuristic warnings (mil/inch detection)
- Tolerance bounds (±0.5mm for geometry)
- Multiple error reporting
- Exception handling (never raises)

**Fixtures:**
- `valid_spec`: Valid QFN16 component specification

### `test_extractor.py`
Tests for the extractor module.

**Coverage:**
- Prompt building
- JSON parsing (plain, markdown-wrapped, extra whitespace)
- Extraction success path
- Retry logic on invalid JSON
- Failure after max retries (ExtractionError)
- VLM response handling

**Key Tests:**
- Mock VLM client calls
- JSON parsing edge cases
- Retry behavior validation

### `test_footprint.py`
Tests for footprint generation.

**Coverage:**
- S-expression structure validity
- Part number inclusion
- Complete pad set generation
- Thermal pad generation
- Coordinate validity
- Layer specifications
- Different part numbers and pitch values
- Various pin counts

**Fixtures:**
- `qfn_spec`: Sample QFN16 footprint specification

### `test_symbol.py`
Tests for symbol generation.

**Coverage:**
- S-expression structure validity
- Part number inclusion
- Reference designator handling
- Pin name and number inclusion
- All pins present
- Different pin types (POWER, GND, SIGNAL)
- Different pin counts
- Symbol properties

**Fixtures:**
- `qfn_symbol`: Sample QFN16 symbol specification

## Test Fixtures

### `fixtures/sample_extracted.json`
Sample extracted component specification for integration testing.

Contains a valid QFN16 specification with all required fields.

## Test Philosophy

- **No mocking of internal modules**: Tests use real Pydantic models, real validation logic
- **Mock external APIs**: VLM clients are mocked to avoid API calls during testing
- **Comprehensive edge cases**: Includes boundary conditions, error paths, and unusual inputs
- **Never raising assertions**: Tests verify that validation never raises, only reports errors

## Coverage Goals

Target: ≥90% code coverage for core modules
- schema.py: 95% (all model variations)
- validator.py: 100% (all rules tested)
- extractor.py: 95% (including retry paths)
- generators/: 90% (all output formats verified)

## Running with Coverage

```bash
pytest tests/ --cov=src/kicadgen --cov-report=html
# Open htmlcov/index.html for detailed report
```
