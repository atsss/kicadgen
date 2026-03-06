"""Command-line interface for kicadgen."""

import argparse
import sys

from dotenv import load_dotenv


def main() -> int:
    """Main entry point for the kicadgen CLI."""
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Generate KiCAD footprint and symbol files from component datasheets using AI extraction",
        prog="kicadgen",
    )

    # Positional argument
    parser.add_argument(
        "input_pdf",
        help="Path to the component datasheet PDF",
    )

    # Required optional arguments
    parser.add_argument(
        "--part-number",
        required=True,
        help="Component part number (e.g., STM32H743)",
    )

    # Optional arguments
    parser.add_argument(
        "--model",
        default="gpt-4o",
        help="VLM model to use (default: gpt-4o)",
        choices=["gpt-4o", "claude-3-5-sonnet", "gemini-1-5-pro"],
    )

    parser.add_argument(
        "--out",
        default="./out",
        help="Output directory for generated files (default: ./out)",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip file writing, only show validation report",
    )

    args = parser.parse_args()

    from kicadgen.pipeline import run
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
