"""Temporary file management utilities."""

import shutil
from pathlib import Path
from tempfile import mkdtemp


class TempImageDir:
    """Context manager for temporary image directories."""

    def __init__(self):
        """Initialize temporary directory."""
        self.path: Path | None = None

    def __enter__(self) -> Path:
        """Create and return temporary directory path."""
        self.path = Path(mkdtemp(prefix="kicadgen_"))
        return self.path

    def __exit__(self, *_) -> None:
        """Clean up temporary directory on exit."""
        if self.path:
            shutil.rmtree(self.path, ignore_errors=True)
