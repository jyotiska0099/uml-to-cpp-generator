"""
parser.py
---------
Parses a PlantUML (.puml) class diagram file using regex and returns
a structured list of class definitions ready for the Jinja2 generator.

Supported PlantUML syntax:
  - Class declarations with attributes and methods
  - Visibility markers: + (public), - (private), # (protected)
  - Attribute format:  [visibility] name : type
  - Method format:     [visibility] name() : return_type
  - Inheritance:       ChildClass <|-- ParentClass  OR  ParentClass --|> ChildClass
  - Association:       ClassA "1" -- "0..*" ClassB
"""

import re
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class Attribute:
    name: str
    type: str
    visibility: str  # "public", "private", "protected"


@dataclass
class Method:
    name: str
    return_type: str
    visibility: str  # "public", "private", "protected"
    parameters: list[str] = field(default_factory=list)


@dataclass
class ClassDef:
    name: str
    attributes: list[Attribute] = field(default_factory=list)
    methods: list[Method] = field(default_factory=list)
    parent: Optional[str] = None          # single inheritance
    associations: list[str] = field(default_factory=list)  # related class names


# ---------------------------------------------------------------------------
# Visibility helper
# ---------------------------------------------------------------------------

VISIBILITY_MAP = {
    "+": "public",
    "-": "private",
    "#": "protected",
}

def _parse_visibility(symbol: str) -> str:
    return VISIBILITY_MAP.get(symbol.strip(), "public")


# ---------------------------------------------------------------------------
# Core parser
# ---------------------------------------------------------------------------

def parse_puml(filepath: str) -> list[ClassDef]:
    """
    Parse a .puml file and return a list of ClassDef objects.

    Args:
        filepath: path to the .puml file

    Returns:
        list of ClassDef dataclass instances
    """
    with open(filepath, "r") as f:
        content = f.read()

    classes: dict[str, ClassDef] = {}

    # -----------------------------------------------------------------------
    # Pass 1 — Extract each class block
    # Pattern: class ClassName { ... }
    # -----------------------------------------------------------------------
    class_block_re = re.compile(
        r'class\s+(\w+)\s*\{([^}]*)\}',
        re.DOTALL
    )

    for match in class_block_re.finditer(content):
        class_name = match.group(1).strip()
        class_body = match.group(2)

        cls = ClassDef(name=class_name)

        # -------------------------------------------------------------------
        # Parse each line inside the class body
        # Attribute: [vis] name : type
        # Method:    [vis] name() : return_type
        # -------------------------------------------------------------------
        line_re = re.compile(
            r'([+\-#])\s*(\w+)(\(.*?\))?\s*:\s*(\w+)'
        )

        for line in class_body.splitlines():
            line = line.strip()
            if not line:
                continue

            m = line_re.match(line)
            if not m:
                continue

            visibility_sym = m.group(1)
            member_name    = m.group(2)
            params_raw     = m.group(3)   # None if attribute, "()" if method
            type_name      = m.group(4)

            visibility = _parse_visibility(visibility_sym)

            if params_raw is not None:
                # It's a method
                params = _parse_params(params_raw)
                cls.methods.append(Method(
                    name=member_name,
                    return_type=type_name,
                    visibility=visibility,
                    parameters=params
                ))
            else:
                # It's an attribute
                cls.attributes.append(Attribute(
                    name=member_name,
                    type=type_name,
                    visibility=visibility
                ))

        classes[class_name] = cls

    # -----------------------------------------------------------------------
    # Pass 2 — Extract inheritance relationships
    # Supports both:
    #   Child <|-- Parent
    #   Parent --|> Child
    # -----------------------------------------------------------------------
    inherit_re_1 = re.compile(r'(\w+)\s*<\|--\s*(\w+)')   # Child <|-- Parent
    inherit_re_2 = re.compile(r'(\w+)\s*--\|>\s*(\w+)')   # Parent --|> Child

    for m in inherit_re_1.finditer(content):
        parent_name = m.group(1)
        child_name  = m.group(2)
        if child_name in classes:
            classes[child_name].parent = parent_name

    for m in inherit_re_2.finditer(content):
        parent_name = m.group(1)
        child_name  = m.group(2)
        if child_name in classes:
            classes[child_name].parent = parent_name

    # -----------------------------------------------------------------------
    # Pass 3 — Extract associations
    # Pattern: ClassA "multiplicity" -- "multiplicity" ClassB
    # -----------------------------------------------------------------------
    assoc_re = re.compile(
        r'(\w+)\s+(?:"[^"]*"\s+)?--\s+(?:"[^"]*"\s+)?(\w+)'
    )

    for m in assoc_re.finditer(content):
        class_a = m.group(1)
        class_b = m.group(2)

        # skip if this line is actually an inheritance arrow
        full_match = m.group(0)
        if "<|" in full_match or "|>" in full_match:
            continue

        if class_a in classes and class_b not in classes[class_a].associations:
            classes[class_a].associations.append(class_b)
        if class_b in classes and class_a not in classes[class_b].associations:
            classes[class_b].associations.append(class_a)

    return list(classes.values())


# ---------------------------------------------------------------------------
# Parameter parser (for method signatures)
# ---------------------------------------------------------------------------

def _parse_params(params_raw: str) -> list[str]:
    """
    Parse method parameter string like "(name : type, age : int)"
    Returns a list of strings like ["name : type", "age : int"]
    """
    # Strip outer parentheses
    inner = params_raw.strip("()")
    if not inner.strip():
        return []
    return [p.strip() for p in inner.split(",") if p.strip()]


# ---------------------------------------------------------------------------
# Debug helper
# ---------------------------------------------------------------------------

def print_parsed(classes: list[ClassDef]) -> None:
    """Pretty-print parsed class definitions to stdout."""
    for cls in classes:
        print(f"\nClass: {cls.name}", end="")
        if cls.parent:
            print(f"  (extends {cls.parent})", end="")
        if cls.associations:
            print(f"  (associated with: {', '.join(cls.associations)})", end="")
        print()

        if cls.attributes:
            print("  Attributes:")
            for attr in cls.attributes:
                print(f"    [{attr.visibility}] {attr.name} : {attr.type}")

        if cls.methods:
            print("  Methods:")
            for method in cls.methods:
                params = ", ".join(method.parameters) if method.parameters else ""
                print(f"    [{method.visibility}] {method.name}({params}) : {method.return_type}")


# ---------------------------------------------------------------------------
# Quick test — run directly to verify: python parser.py
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    import os

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
        print(f"Parsing: {path}")
        print('='*50)
        result = parse_puml(path)
        print_parsed(result)