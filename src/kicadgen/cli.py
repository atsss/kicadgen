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

    # Positional argument (optional if --input-json is provided)
    parser.add_argument(
        "input_pdf",
        nargs="?",
        default=None,
        help="Path to the component datasheet PDF (not required if --input-json is provided)",
    )

    # Required optional arguments
    parser.add_argument(
        "--part-number",
        required=True,
        help="Component part number (e.g., STM32H743)",
    )

    # JSON input option (skips VLM extraction)
    parser.add_argument(
        "--input-json",
        metavar="PATH",
        default=None,
        help="Path to a pre-extracted JSON file; skips VLM extraction stage",
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

    parser.add_argument(
        "--no-review",
        action="store_true",
        help="Skip human review of extracted JSON before validation",
    )

    args = parser.parse_args()

    # Validate that either input_pdf or --input-json is provided, but not both
    if args.input_pdf is None and args.input_json is None:
        parser.error(
            "either INPUT_PDF or --input-json must be provided"
        )

    if args.input_pdf is not None and args.input_json is not None:
        parser.error(
            "cannot provide both INPUT_PDF and --input-json; choose one"
        )

    from kicadgen.pipeline import run

    return run(args)


if __name__ == "__main__":
    sys.exit(main())
