from __future__ import annotations

import argparse
from pathlib import Path

import ezdxf


DEFAULT_VALUES = {
    "CANTI7_UP": 1234,
    "CANTI7_DOWN": 5678,
    "POLE_1": 9999,
}


def parse_value(value: str) -> tuple[str, str]:
    if "=" not in value:
        raise argparse.ArgumentTypeError(f"Expected KEY=VALUE, got {value!r}")
    key, replacement = value.split("=", 1)
    key = key.strip()
    replacement = replacement.strip()
    if not key:
        raise argparse.ArgumentTypeError(f"Missing dimension ID in {value!r}")
    return key, replacement


def entity_text(entity) -> str:
    if entity.dxftype() == "TEXT":
        return entity.dxf.text or ""
    if entity.dxftype() == "MTEXT":
        return entity.plain_text() if hasattr(entity, "plain_text") else entity.text
    return ""


def set_entity_text(entity, value: str) -> None:
    if entity.dxftype() == "TEXT":
        entity.dxf.text = value
    elif entity.dxftype() == "MTEXT":
        if hasattr(entity, "set_content"):
            entity.set_content(value)
        else:
            entity.text = value


def replace_rendered_dimension_block_text(doc, dim, dimension_id: str, value: str) -> int:
    block_name = dim.dxf.get("geometry")
    if not block_name or block_name not in doc.blocks:
        return 0

    replacements = 0
    block = doc.blocks[block_name]
    for entity in block:
        if entity.dxftype() not in {"TEXT", "MTEXT"}:
            continue
        if entity_text(entity).strip() == dimension_id:
            set_entity_text(entity, value)
            replacements += 1
    return replacements


def replace_dimension_values(template_path: Path, output_path: Path, values: dict[str, object]) -> tuple[int, int]:
    doc = ezdxf.readfile(template_path)
    msp = doc.modelspace()
    override_replacements = 0
    rendered_replacements = 0

    for dim in msp.query("DIMENSION"):
        dimension_id = (dim.dxf.text or "").strip()
        if dimension_id in values:
            value = str(values[dimension_id])
            dim.dxf.text = value
            override_replacements += 1
            rendered_replacements += replace_rendered_dimension_block_text(doc, dim, dimension_id, value)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(output_path)
    return override_replacements, rendered_replacements


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a test DXF by replacing DIMENSION text override IDs with explicit values."
    )
    parser.add_argument(
        "--template",
        default="templates/template_TYPE1.dxf",
        help="Template DXF path. Default: templates/template_TYPE1.dxf",
    )
    parser.add_argument(
        "--output",
        default="output/test_dimension_values.dxf",
        help="Output DXF path. Default: output/test_dimension_values.dxf",
    )
    parser.add_argument(
        "--value",
        action="append",
        type=parse_value,
        help="Dimension replacement as ID=VALUE. Can be repeated.",
    )
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent
    template_path = (base_dir / args.template).resolve()
    output_path = (base_dir / args.output).resolve()
    values = dict(args.value) if args.value else DEFAULT_VALUES

    override_replacements, rendered_replacements = replace_dimension_values(template_path, output_path, values)
    print(f"Wrote {output_path}")
    print(f"Replaced {override_replacements} DIMENSION text override(s)")
    print(f"Replaced {rendered_replacements} rendered dimension text object(s)")
    print("Values:")
    for key, value in values.items():
        print(f"  {key} -> {value}")


if __name__ == "__main__":
    main()
