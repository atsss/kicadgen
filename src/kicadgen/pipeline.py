"""Pipeline orchestration for the complete extraction and generation workflow."""

import json
import logging
from pathlib import Path

import fitz  # type: ignore[import-untyped]

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


def prompt_human_review(spec, extracted_path: Path) -> bool:
    """
    Prompt user to review extracted specification before validation.

    Displays a summary of key extracted fields and asks user to confirm.

    Args:
        spec: ComponentSpec from extraction
        extracted_path: Path to extracted.json file

    Returns:
        True to proceed with validation, False to abort pipeline
    """
    # Build summary
    lines = [
        "",
        "─" * 60,
        " Extracted Specification Review",
        "─" * 60,
    ]

    # Component info
    lines.append(f" Component : {spec.component.name} ({spec.component.manufacturer})")
    lines.append(f" Part No.  : {spec.component.part_number}")
    lines.append(f" Package   : {spec.component.package_type}")

    # Confidence
    confidence_pct = spec.metadata.extraction_confidence * 100
    confidence_str = f"{confidence_pct:.1f}%"
    if spec.metadata.extraction_confidence < 0.8:
        confidence_str += " ⚠️ LOW"
    lines.append(f" Confidence: {confidence_str}")

    # Footprint info
    lines.append("")
    footprint_desc = f"{spec.footprint.pin_count} pads"
    if spec.footprint.pins_per_side is not None:
        footprint_desc += f", {spec.footprint.pins_per_side}/side"
    if spec.footprint.pitch_mm is not None:
        footprint_desc += f", pitch {spec.footprint.pitch_mm}mm"
    footprint_desc += f" ({spec.footprint.pad_type})"
    lines.append(f" Footprint : {footprint_desc}")

    # Missing fields
    if spec.metadata.missing_fields:
        lines.append(f" Missing   : {', '.join(spec.metadata.missing_fields)}")

    # Assumptions
    if spec.metadata.assumptions:
        lines.append(f" Assumed   : {spec.metadata.assumptions[0]}")
        if len(spec.metadata.assumptions) > 1:
            for assumption in spec.metadata.assumptions[1:]:
                lines.append(f"             {assumption}")

    # File path
    lines.append("")
    lines.append(f" Full JSON : {extracted_path}")
    lines.append("─" * 60)

    # Print summary
    print("\n".join(lines))

    # Prompt user
    while True:
        response = input("Proceed with validation? [Y/n]: ").strip().lower()
        if response in ("", "y", "yes"):
            return True
        elif response in ("n", "no", "q", "quit"):
            return False
        else:
            print("Please enter 'y' to continue or 'n' to abort.")


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

        # Human review (unless --no-review)
        if not args.no_review:
            if not prompt_human_review(spec, extracted_path):
                logger.info("Review aborted by user")
                return 1

        # Validate
        logger.info("Validating component specification...")
        report = validate_component(spec)

        # Write validation report
        report_path = output_dir / "validation_report.txt"
        write_validation_report(report, report_path)
        logger.info(f"Saved validation report to {report_path}")

        # Check for confidence warning
        if spec.metadata.extraction_confidence < 0.8:
            logger.warning(
                f"Low confidence ({spec.metadata.extraction_confidence:.1%}): results may be inaccurate"
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
