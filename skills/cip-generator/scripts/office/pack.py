"""Pack a directory into a DOCX, PPTX, or XLSX file.

Validates with auto-repair, condenses XML formatting, and creates the Office file.

PATCH v2: Normalizes absolute OPC relationship targets to relative paths before
zipping. Absolute paths (e.g. /ppt/slides/slide1.xml) cause PowerPoint to fail
to load the file because the ZIP stores entries without the leading slash.

Usage:
    python pack.py <input_directory> <output_file> [--original <file>]

Examples:
    python pack.py unpacked/ output.pptx --original input.pptx
"""

import argparse
import re
import sys
import shutil
import tempfile
import zipfile
from pathlib import Path

import defusedxml.minidom

from validators import DOCXSchemaValidator, PPTXSchemaValidator, RedliningValidator


def _relative_target(abs_target: str, rels_path: str) -> str:
    """Convert an absolute OPC target to a path relative to the .rels file."""
    target_parts = abs_target.lstrip("/").split("/")
    rels_dir_parts = rels_path.split("/")[:-1]

    common = 0
    for a, b in zip(rels_dir_parts, target_parts):
        if a == b:
            common += 1
        else:
            break

    ups = len(rels_dir_parts) - common
    return "../" * ups + "/".join(target_parts[common:])


def _normalize_rels_paths(content: bytes, rels_filepath: str) -> bytes:
    """Rewrite absolute Target= values in a .rels file to relative paths."""
    text = content.decode("utf-8")

    def replacer(match):
        target = match.group(1)
        if target.startswith("/"):
            return 'Target="{}"'.format(_relative_target(target, rels_filepath))
        return match.group(0)

    return re.sub(r'Target="([^"]*)"', replacer, text).encode("utf-8")


def pack(
    input_directory: str,
    output_file: str,
    original_file=None,
    validate: bool = True,
    infer_author_func=None,
):
    input_dir = Path(input_directory)
    output_path = Path(output_file)
    suffix = output_path.suffix.lower()

    if not input_dir.is_dir():
        return None, f"Error: {input_dir} is not a directory"

    if suffix not in {".docx", ".pptx", ".xlsx"}:
        return None, f"Error: {output_file} must be a .docx, .pptx, or .xlsx file"

    if validate and original_file:
        original_path = Path(original_file)
        if original_path.exists():
            success, output = _run_validation(
                input_dir, original_path, suffix, infer_author_func
            )
            if output:
                print(output)
            if not success:
                return None, f"Error: Validation failed for {input_dir}"

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_content_dir = Path(temp_dir) / "content"
        shutil.copytree(input_dir, temp_content_dir)

        for pattern in ["*.xml", "*.rels"]:
            for xml_file in temp_content_dir.rglob(pattern):
                _condense_xml(xml_file)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in temp_content_dir.rglob("*"):
                if f.is_file():
                    arcname = str(f.relative_to(temp_content_dir))
                    data = f.read_bytes()
                    if arcname.endswith(".rels"):
                        data = _normalize_rels_paths(data, arcname)
                    zf.writestr(arcname, data)

    return None, f"Successfully packed {input_dir} to {output_file}"


def _run_validation(unpacked_dir, original_file, suffix, infer_author_func=None):
    output_lines = []
    validators = []

    if suffix == ".docx":
        author = "Claude"
        if infer_author_func:
            try:
                author = infer_author_func(unpacked_dir, original_file)
            except ValueError as e:
                print(f"Warning: {e} Using default author 'Claude'.", file=sys.stderr)
        validators = [
            DOCXSchemaValidator(unpacked_dir, original_file),
            RedliningValidator(unpacked_dir, original_file, author=author),
        ]
    elif suffix == ".pptx":
        validators = [PPTXSchemaValidator(unpacked_dir, original_file)]

    if not validators:
        return True, None

    total_repairs = sum(v.repair() for v in validators)
    if total_repairs:
        output_lines.append(f"Auto-repaired {total_repairs} issue(s)")

    success = all(v.validate() for v in validators)
    if success:
        output_lines.append("All validations PASSED!")

    return success, "\n".join(output_lines) if output_lines else None


def _condense_xml(xml_file: Path) -> None:
    try:
        with open(xml_file, encoding="utf-8") as f:
            dom = defusedxml.minidom.parse(f)
        for element in dom.getElementsByTagName("*"):
            if element.tagName.endswith(":t"):
                continue
            for child in list(element.childNodes):
                if (
                    child.nodeType == child.TEXT_NODE
                    and child.nodeValue
                    and child.nodeValue.strip() == ""
                ) or child.nodeType == child.COMMENT_NODE:
                    element.removeChild(child)
        xml_file.write_bytes(dom.toxml(encoding="UTF-8"))
    except Exception as e:
        print(f"ERROR: Failed to parse {xml_file.name}: {e}", file=sys.stderr)
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_directory")
    parser.add_argument("output_file")
    parser.add_argument("--original")
    parser.add_argument("--validate", type=lambda x: x.lower() == "true", default=True)
    args = parser.parse_args()

    _, message = pack(
        args.input_directory,
        args.output_file,
        original_file=args.original,
        validate=args.validate,
    )
    print(message)
    if "Error" in message:
        sys.exit(1)
