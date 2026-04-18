"""
main.py
-------
CLI entry point for the UML-to-C++ code generator.

Usage:
    python main.py --input samples/vehicle.puml
    python main.py --input samples/shapes.puml --output output/ --verbose
    python main.py --input samples/library.puml --output my_output/ --verbose
"""

import argparse
import os
import sys

from parser import parse_puml, print_parsed
from generator import generate


# ---------------------------------------------------------------------------
# Argument parser setup
# ---------------------------------------------------------------------------

def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="uml-to-cpp",
        description="Generate C++ skeleton code from a PlantUML class diagram.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
Examples:
  python main.py --input samples/vehicle.puml
  python main.py --input samples/shapes.puml --output output/ --verbose
  python main.py --input samples/library.puml --output my_output/
        """
    )

    parser.add_argument(
        "--input", "-i",
        required=True,
        metavar="FILE",
        help="Path to the input .puml file"
    )

    parser.add_argument(
        "--output", "-o",
        default="output/",
        metavar="DIR",
        help="Directory to write generated .h and .cpp files (default: output/)"
    )

    parser.add_argument(
        "--templates", "-t",
        default="templates/",
        metavar="DIR",
        help="Directory containing Jinja2 templates (default: templates/)"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print parsed class info and generated file paths"
    )

    return parser


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def validate_args(args: argparse.Namespace) -> None:
    """Validate input file and template directory exist."""

    if not os.path.isfile(args.input):
        print(f"[ERROR] Input file not found: {args.input}")
        sys.exit(1)

    if not args.input.endswith(".puml"):
        print(f"[WARNING] Input file does not have a .puml extension: {args.input}")

    if not os.path.isdir(args.templates):
        print(f"[ERROR] Templates directory not found: {args.templates}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    arg_parser = build_arg_parser()
    args = arg_parser.parse_args()

    validate_args(args)

    # -------------------------------------------------------------------
    # Step 1 — Parse
    # -------------------------------------------------------------------
    print(f"\n[1/2] Parsing: {args.input}")

    classes = parse_puml(args.input)

    if not classes:
        print("[ERROR] No classes found in the input file. Check your .puml syntax.")
        sys.exit(1)

    print(f"      Found {len(classes)} class(es): {', '.join(c.name for c in classes)}")

    if args.verbose:
        print()
        print_parsed(classes)

    # -------------------------------------------------------------------
    # Step 2 — Generate
    # -------------------------------------------------------------------
    print(f"\n[2/2] Generating C++ files into: {args.output}")

    generated = generate(
        classes,
        output_dir=args.output,
        template_dir=args.templates,
        verbose=args.verbose
    )

    # -------------------------------------------------------------------
    # Summary
    # -------------------------------------------------------------------
    print(f"\n✓ Done. {len(generated)} file(s) generated:\n")
    for filepath in generated:
        print(f"  {filepath}")
    print()


if __name__ == "__main__":
    main()