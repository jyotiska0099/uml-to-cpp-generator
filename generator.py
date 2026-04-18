"""
generator.py
------------
Takes a list of ClassDef objects (from parser.py) and renders
C++ header (.h) and source (.cpp) files using Jinja2 templates.

Usage (as a module):
    from generator import generate
    generate(classes, output_dir="output/", template_dir="templates/")
"""

import os
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from parser import ClassDef


# ---------------------------------------------------------------------------
# Main generator function
# ---------------------------------------------------------------------------

def generate(
    classes: list[ClassDef],
    output_dir: str = "output/",
    template_dir: str = "templates/",
    verbose: bool = False
) -> list[str]:
    """
    Render .h and .cpp files for each ClassDef using Jinja2 templates.

    Args:
        classes:      list of ClassDef objects from parser.parse_puml()
        output_dir:   directory where generated files will be written
        template_dir: directory containing header.h.j2 and source.cpp.j2
        verbose:      if True, print each file path as it is written

    Returns:
        list of file paths that were generated
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Set up Jinja2 environment
    # StrictUndefined raises an error if a template variable is missing
    env = Environment(
        loader=FileSystemLoader(template_dir),
        undefined=StrictUndefined,
        trim_blocks=True,       # removes newline after block tags
        lstrip_blocks=True,     # strips leading whitespace from block tags
    )

    header_template = env.get_template("header.h.j2")
    source_template = env.get_template("source.cpp.j2")

    generated_files = []

    for cls in classes:
        context = {"cls": cls}

        # -------------------------------------------------------------------
        # Render and write the header file
        # -------------------------------------------------------------------
        header_content = header_template.render(context)
        header_path = os.path.join(output_dir, f"{cls.name}.h")

        with open(header_path, "w") as f:
            f.write(header_content)

        generated_files.append(header_path)
        if verbose:
            print(f"  [+] Written: {header_path}")

        # -------------------------------------------------------------------
        # Render and write the source file
        # -------------------------------------------------------------------
        source_content = source_template.render(context)
        source_path = os.path.join(output_dir, f"{cls.name}.cpp")

        with open(source_path, "w") as f:
            f.write(source_content)

        generated_files.append(source_path)
        if verbose:
            print(f"  [+] Written: {source_path}")

    return generated_files


# ---------------------------------------------------------------------------
# Quick test — run directly: python generator.py
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from parser import parse_puml, print_parsed

    test_files = [
        "samples/vehicle.puml",
        "samples/shapes.puml",
        "samples/library.puml",
    ]

    for path in test_files:
        if not os.path.exists(path):
            print(f"[SKIP] {path} not found")
            continue

        print(f"\n{'='*50}")
        print(f"Generating from: {path}")
        print('='*50)

        classes = parse_puml(path)

        # Use a subdirectory per diagram to keep output organised
        diagram_name = os.path.splitext(os.path.basename(path))[0]
        out_dir = os.path.join("output", diagram_name)

        files = generate(classes, output_dir=out_dir, verbose=True)

    print(f"\nDone. Check the output/ directory.")