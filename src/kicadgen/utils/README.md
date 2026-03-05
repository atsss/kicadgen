# utils

Utility modules for logging and temporary file management.

## Module Overview

### `__init__.py`
Package initialization for utils subpackage.

### `logging.py`
Logging configuration utilities.

**Functions:**
- `setup_logger(name, verbose)`: Configures a logger with appropriate verbosity level

**Features:**
- Outputs to stderr
- Formats messages with timestamp, logger name, level, and message
- DEBUG level when verbose=True, INFO otherwise
- Returns configured logger instance

**Usage:**
```python
from kicadgen.utils.logging import setup_logger

logger = setup_logger(__name__, verbose=args.verbose)
logger.info("Processing started")
```

### `tempfiles.py`
Context manager for temporary directory management.

**Classes:**
- `TempImageDir`: Context manager for creating and cleaning up temporary directories

**Features:**
- Creates temporary directory with `kicadgen_` prefix
- Automatically cleans up directory tree on exit
- Uses `ignore_errors=True` for robust cleanup (doesn't fail if files are locked)

**Usage:**
```python
from kicadgen.utils.tempfiles import TempImageDir

with TempImageDir() as tmpdir:
    # tmpdir is a Path object pointing to temporary directory
    image_path = tmpdir / "image.png"
    image_path.write_bytes(png_data)
# Directory automatically cleaned up on exit
```

## Security Notes

- Temporary directories are created in the system default temp location
- Temporary images are deleted immediately after processing (even on errors)
- No API keys or sensitive data should be written to temporary files
