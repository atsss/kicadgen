"""Pipeline orchestration for the complete extraction and generation workflow."""

import json
import logging
from pathlib import Path

import fitz

from kicadgen.extractor import extract
from kicadgen.generators.footprint import generate_footprint_sexpr
from kicadgen.generators.symbol import generate_symbol_sexpr
from kicadgen.pdf_processor import render_pages_to_png, select_relevant_pages
from kicadgen.utils.logging import setup_logger
from kicadgen.utils.tempfiles import TempImageDir
from kicadgen.validator import validate_component
from kicadgen.vlm_client import get_client

logger = setup_logger(__name__)

# Keywords to search for in PDF
KEYWORDS = ["Recommended Land Pattern", "Package Dimensions", "Pin Configuration"]


def write_validation_report(report, output_path: Path) -> None:
    """Write validation report to text file."""
    lines = []
    if report.is_valid:
        lines.append("✓ Validation PASSED")
    else:
        lines.append("✗ Validation FAILED")

    if report.errors:
        lines.append("\nErrors:")
        for error in report.errors:
            lines.append(f"  - {error}")

    if report.warnings:
        lines.append("\nWarnings:")
        for warning in report.warnings:
            lines.append(f"  - {warning}")

    output_path.write_text("\n".join(lines) + "\n")


def run(args) -> int:
    """
    Run the complete pipeline.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    # Set up logging
    logger = setup_logger(__name__, verbose=args.verbose)

    # Validate input file
    input_path = Path(args.input_pdf)
    if not input_path.exists():
        logger.error(f"Input PDF not found: {input_path}")
        return 1

    # Create output directory
    output_dir = Path(args.out)
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Load PDF
        logger.info(f"Loading PDF: {input_path}")
        doc = fitz.open(input_path)

        # Select relevant pages
        logger.info("Selecting relevant pages...")
        page_indices = select_relevant_pages(doc, KEYWORDS)
        if not page_indices:
            logger.warning("No relevant pages found; using first page")
            page_indices = [0]

        # Render pages to images
        logger.info(f"Rendering {len(page_indices)} page(s) to PNG...")
        with TempImageDir() as tmpdir:
            images = render_pages_to_png(doc, page_indices, dpi=300)

            # Get VLM client
            logger.info(f"Initializing VLM client for model: {args.model}")
            client = get_client(args.model)

            # Extract component specification
            logger.info("Extracting component specification from VLM...")
            spec = extract(client, images, args.part_number)

        # Save extracted JSON
        extracted_path = output_dir / "extracted.json"
        extracted_path.write_text(spec.model_dump_json(indent=2))
        logger.info(f"Saved extracted specification to {extracted_path}")

        # Validate
        logger.info("Validating component specification...")
        report = validate_component(spec)

        # Write validation report
        report_path = output_dir / "validation_report.txt"
        write_validation_report(report, report_path)
        logger.info(f"Saved validation report to {report_path}")

        # Check for confidence warning
        if spec.meta.confidence < 0.8:
            logger.warning(
                f"Low confidence ({spec.meta.confidence:.1%}): results may be inaccurate"
            )

        # Check validation result
        if not report.is_valid:
            logger.error("Validation failed; skipping KiCAD file generation")
            return 1

        # Generate KiCAD files (unless --dry-run)
        if not args.dry_run:
            logger.info("Generating KiCAD files...")

            # Generate footprint
            footprint_sexpr = generate_footprint_sexpr(spec.footprint, args.part_number)
            footprint_path = output_dir / f"{args.part_number}.kicad_mod"
            footprint_path.write_text(footprint_sexpr)
            logger.info(f"Saved footprint to {footprint_path}")

            # Generate symbol
            symbol_sexpr = generate_symbol_sexpr(spec.symbol, args.part_number)
            symbol_path = output_dir / f"{args.part_number}.kicad_sym"
            symbol_path.write_text(symbol_sexpr)
            logger.info(f"Saved symbol to {symbol_path}")
        else:
            logger.info("--dry-run: Skipping KiCAD file generation")

        logger.info("Pipeline completed successfully")
        return 0

    except Exception as e:
        logger.error(f"Pipeline error: {e}", exc_info=True)
        return 1
