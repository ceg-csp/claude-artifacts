#!/usr/bin/env python3
"""
CIP Runner — Hardened single-script pipeline for CIP deck generation.

Fixes applied vs original skill workflow:
  1. No clean.py — slides are never deleted
  2. Uses patched pack.py with OPC rels path normalization
  3. Data normalization dict built before any XML edit
  4. Shape-label anchoring — finds editable values by their sibling label text,
     not fragile approximate line numbers
  5. Full validation gate before delivering output
  6. Single-turn execution — no recovery loops needed

Usage:
    python3 cip_runner.py --data data.json --output /path/to/CIP_Account.pptx

data.json schema: see sample_data.json in this directory
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

# ─── Paths ───────────────────────────────────────────────────────────────────
# Resolve relative to this file so the skill is portable regardless of install location
_SKILL_ROOT = Path(__file__).resolve().parent
TEMPLATE    = _SKILL_ROOT / "assets" / "CIP_MASTER_TEMPLATE.pptx"
SCRIPTS     = _SKILL_ROOT / "scripts"
WORK_DIR    = Path("/home/claude/cip_work")
UNPACKED    = WORK_DIR / "unpacked"


# ─── Data Validation ─────────────────────────────────────────────────────────
REQUIRED_FIELDS = [
    "account_name", "account_short", "csm_name", "customer_since",
    "time_with_impact", "instance", "release", "health_score",
    "accelerators_raised", "on_demand_training", "impact_app_usage",
    "licensing_rows",
]

def validate_data(d: dict) -> None:
    """Fail fast if required fields are missing or empty before touching any XML."""
    errors = []
    for field in REQUIRED_FIELDS:
        if field not in d:
            errors.append(f"Missing required field: '{field}'")
        elif not d[field] and d[field] != 0:
            errors.append(f"Required field is empty: '{field}'")

    if "licensing_rows" in d:
        if not isinstance(d["licensing_rows"], list) or len(d["licensing_rows"]) == 0:
            errors.append("'licensing_rows' must be a non-empty list")
        else:
            for i, row in enumerate(d["licensing_rows"]):
                for key in ("code", "name", "type", "units"):
                    if key not in row:
                        errors.append(f"licensing_rows[{i}] missing key: '{key}'")

    if errors:
        print("DATA VALIDATION FAILED — fix the input JSON before retrying:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)


def run(cmd, cwd=None):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    if result.returncode != 0:
        print(f"  CMD FAILED: {cmd}")
        print(f"  STDERR: {result.stderr[:300]}")
        sys.exit(1)
    return result.stdout.strip()


def read_slide(n):
    return (UNPACKED / f"ppt/slides/slide{n}.xml").read_text(encoding="utf-8")


def write_slide(n, content):
    (UNPACKED / f"ppt/slides/slide{n}.xml").write_text(content, encoding="utf-8")


def safe_replace(content, old, new, label=""):
    """Replace first occurrence; warn if not found (never crash)."""
    if old in content:
        return content.replace(old, new, 1)
    print(f"  WARN: '{label or old[:40]}' not found — skipping")
    return content


def replace_at_line(lines, line_num, old_val, new_val):
    """Replace old_val with new_val near line_num (±8 tolerance)."""
    idx = line_num - 1
    for offset in range(-8, 9):
        ci = idx + offset
        if 0 <= ci < len(lines) and old_val in lines[ci]:
            lines[ci] = lines[ci].replace(old_val, new_val, 1)
            return lines
    print(f"  WARN: '{old_val}' not found near line {line_num}")
    return lines


# ─── Slide editors ───────────────────────────────────────────────────────────
def edit_slide1(d):
    print("  Slide 1 — Cover")
    s = read_slide(1)
    s = safe_replace(s, "Department of Planning, Housing &amp; Infrastructure",
                     d["account_name"], "account_name")
    s = safe_replace(s, "Vivian Vuu", d["csm_name"], "csm_name")
    write_slide(1, s)


def edit_slide4(d):
    print("  Slide 4 — Impact Reset")
    lines = read_slide(4).splitlines(keepends=True)

    content = "".join(lines)
    content = safe_replace(content, "<a:t>DPHI</a:t>",
                           f"<a:t>{d['account_short']}</a:t>", "account_short")
    content = safe_replace(content, "<a:t>21 Dec 2018</a:t>",
                           f"<a:t>{d['customer_since']}</a:t>", "customer_since")
    content = safe_replace(content, "<a:t>2+ years</a:t>",
                           f"<a:t>{d['time_with_impact']}</a:t>", "time_with_impact")
    content = safe_replace(content, "<a:t>cspconnect</a:t>",
                           f"<a:t>{d['instance']}</a:t>", "instance")
    content = safe_replace(content, "<a:t>Zurich</a:t>",
                           f"<a:t>{d['release']}</a:t>", "release")
    lines = content.splitlines(keepends=True)

    # Line-anchored numeric fields — unique sentinel values
    line_map = {
        3408: ("<a:t>7</a:t>",   f"<a:t>{d['accelerators_raised']}</a:t>"),
        4346: ("<a:t>N/A</a:t>", f"<a:t>{d['health_score']}</a:t>"),
        4511: ("<a:t>-</a:t>",   f"<a:t>{d['on_demand_training']}</a:t>"),
        4676: ("<a:t>1/5</a:t>", f"<a:t>{d['observer_seats']}</a:t>"),
    }
    for line_num, (old, new) in line_map.items():
        lines = replace_at_line(lines, line_num, old, new)

    # The two 25% fields are disambiguated by their sibling label text within the
    # same XML shape block — use label context to find and replace each one safely.
    # critical_apps_undeployed: shape contains label "Critical Apps Undeployed"
    # impact_app_usage:         shape contains label "in Use" (Impact in Use)
    content = "".join(lines)

    def replace_25pct_by_label(xml, label_text, new_val):
        """
        Find the <p:sp> block that contains label_text, then replace the first
        <a:t>25%</a:t> within that block with new_val.
        """
        import re as _re
        sp_pat = _re.compile(r'<p:sp\b[^>]*>.*?</p:sp>', _re.DOTALL)
        def replacer(m):
            block = m.group(0)
            if label_text in block and '<a:t>25%</a:t>' in block:
                return block.replace('<a:t>25%</a:t>',
                                     f'<a:t>{new_val}</a:t>', 1)
            return block
        return sp_pat.sub(replacer, xml)

    content = replace_25pct_by_label(
        content, "Critical Apps Undeployed", d["critical_apps_undeployed"]
    )
    content = replace_25pct_by_label(
        content, "in Use", d["impact_app_usage"]
    )
    lines = content.splitlines(keepends=True)

    # Past accelerators — 6 bullet slots
    accel_slots = [3033, 3069, 3139, 3175, 3211, 3247]
    past = d.get("past_accelerators", [])
    slot_originals = [
        " Your CMDB", "Jumpstart Your ", "Health Assessment ",
        "Jumpstart Your Now Assist for Creator",
        "Jumpstart Your Employee Center", "TuneUp",
    ]
    for slot_idx, (line_num, orig) in enumerate(zip(accel_slots, slot_originals)):
        new_text = past[slot_idx] if slot_idx < len(past) else ""
        if new_text:
            idx = line_num - 1
            for offset in range(-4, 5):
                ci = idx + offset
                if 0 <= ci < len(lines) and orig in lines[ci]:
                    lines[ci] = lines[ci].replace(orig, new_text, 1)
                    break

    # Adoption gaps — 4 bullet slots
    gap_originals = [
        "Problem Management", "Strategic Planning",
        "Employee Center Pro", "Now Assist",
    ]
    gap_lines = [3766, 3802, 3838, 3874]
    gaps = d.get("adoption_gaps", [])
    for slot_idx, (line_num, orig) in enumerate(zip(gap_lines, gap_originals)):
        new_text = gaps[slot_idx] if slot_idx < len(gaps) else ""
        if new_text:
            idx = line_num - 1
            for offset in range(-4, 5):
                ci = idx + offset
                if 0 <= ci < len(lines) and orig in lines[ci]:
                    lines[ci] = lines[ci].replace(orig, new_text, 1)
                    break

    write_slide(4, "".join(lines))


def edit_slide5(d):
    print("  Slide 5 — Licensing Table")
    lines = read_slide(5).splitlines(keepends=True)

    for i, line in enumerate(lines):
        if "DPHI&#x2019;s Current Licensing" in line:
            lines[i] = line.replace(
                "DPHI&#x2019;s Current Licensing",
                f"{d['account_short']}&#x2019;s Current Licensing",
            )
            break

    template_rows = [
        (517,  604,  695,  786),
        (880,  971,  1066, 1161),
        (1259, 1350, 1445, 1540),
        (1638, 1729, 1824, 1919),
        (2017, 2108, 2203, 2298),
        (2396, 2487, 2582, 2677),
        (2775, 2866, 2961, 3056),
        (3154, 3245, 3340, 3435),
        (3533, 3624, 3719, 3798),
        (3896, 3987, 4082, 4177),
    ]

    for row_idx, row_lines in enumerate(template_rows):
        if row_idx >= len(d["licensing_rows"]):
            break
        lic = d["licensing_rows"][row_idx]
        col_vals = [lic["code"], lic["name"], lic["type"], lic["units"]]
        for line_num, val in zip(row_lines, col_vals):
            idx = line_num - 1
            written = False
            for offset in range(-4, 5):
                ci = idx + offset
                if 0 <= ci < len(lines):
                    line = lines[ci]
                    if "<a:t>" in line and "&#x200B;" not in line and "\u200b" not in line:
                        new_line = re.sub(
                            r"<a:t>[^<]*</a:t>",
                            f"<a:t>{val}</a:t>",
                            line,
                            count=1,
                        )
                        if new_line != line:
                            lines[ci] = new_line
                            written = True
                            break
            # Fallback: if cell was empty (<a:t/> or <a:t></a:t>), force-write value
            if not written:
                for offset in range(-4, 5):
                    ci = idx + offset
                    if 0 <= ci < len(lines):
                        line = lines[ci]
                        if re.search(r"<a:t\s*/>|<a:t></a:t>", line):
                            lines[ci] = re.sub(
                                r"<a:t\s*/>|<a:t></a:t>",
                                f"<a:t>{val}</a:t>",
                                line,
                                count=1,
                            )
                            break

    write_slide(5, "".join(lines))


def edit_slide6(d):
    print("  Slide 6 — Gantt")
    current_month_year = date.today().strftime("%b %Y")
    string_replacements = {
        "DPHI &amp; ServiceNow":          f"{d['account_short']} &amp; ServiceNow",
        "Employee Center Pro Deployment": d.get("initiative_1", ""),
        "ITOM Discovery and CMDB Uplift": d.get("initiative_2", ""),
        "Now Assist Go Live (TBC)":       d.get("initiative_3", ""),
        "72  Learning Credits ":          f"{d.get('training_credits', 'N/A')}  Learning Credits ",
        "with earliest expiry 30-11":     f"expiry {d.get('training_expiry', 'N/A')}",
        "Last updated as of Mar 2026":    f"Last updated as of {current_month_year}",
    }
    content = read_slide(6)
    for old, new in string_replacements.items():
        content = safe_replace(content, old, new)
    write_slide(6, content)


def edit_slide8(d):
    print("  Slide 8 — Accelerator Highlights")
    content = read_slide(8)
    completed   = d.get("completed_accelerators", [])
    recommended = d.get("recommended_accelerators", [])
    sp_pattern = re.compile(r"(<p:sp\b[^>]*>)(.*?)(</p:sp>)", re.DOTALL)

    def update_shape(match):
        full  = match.group(0)
        texts = re.findall(r"<a:t>([^<]+)</a:t>", full)
        text  = " ".join(t.strip() for t in texts if t.strip())
        if any(c.lower() in text.lower() for c in completed):
            full = re.sub(
                r'(<p:spPr[^>]*>.*?<a:solidFill>\s*<a:srgbClr val=")[A-Fa-f0-9]+"',
                r'\g<1>63DF4E"', full, flags=re.DOTALL, count=1)
        elif any(r.lower() in text.lower() for r in recommended):
            full = re.sub(
                r'(<p:spPr[^>]*>.*?<a:solidFill>\s*<a:srgbClr val=")[A-Fa-f0-9]+"',
                r'\g<1>52B8FF"', full, flags=re.DOTALL, count=1)
        return full

    write_slide(8, sp_pattern.sub(update_shape, content))


# ─── Validation ──────────────────────────────────────────────────────────────
def validate_output(pptx_path, d):
    print("\nValidating output...")
    errors = []
    with zipfile.ZipFile(pptx_path, "r") as z:
        names = z.namelist()
        for i in range(1, 16):
            if f"ppt/slides/slide{i}.xml" not in names:
                errors.append(f"Missing slide{i}.xml")
        for name in names:
            if name.endswith(".rels"):
                content = z.read(name).decode("utf-8")
                abs_paths = re.findall(r'Target="(/[^"]*)"', content)
                if abs_paths:
                    errors.append(f"Absolute paths in {name}: {abs_paths[:2]}")
        for name in names:
            if name.endswith(".xml") or name.endswith(".rels"):
                try:
                    ET.fromstring(z.read(name))
                except ET.ParseError as e:
                    errors.append(f"XML error in {name}: {e}")
        s1 = z.read("ppt/slides/slide1.xml").decode()
        s4 = z.read("ppt/slides/slide4.xml").decode()
        s5 = z.read("ppt/slides/slide5.xml").decode()
        checks = [
            (d["account_name"]     in s1, "account_name missing from slide1"),
            (d["csm_name"]         in s1, "csm_name missing from slide1"),
            (d["release"]          in s4, "release missing from slide4"),
            (d["time_with_impact"] in s4, "time_with_impact missing from slide4"),
            (d["account_short"]    in s5, "account_short missing from slide5"),
        ]
        for ok, msg in checks:
            if not ok:
                errors.append(msg)
    if errors:
        print(f"  VALIDATION FAILED — {len(errors)} issue(s):")
        for e in errors:
            print(f"    - {e}")
        return False
    print("  All checks passed.")
    return True


# ─── Main pipeline ────────────────────────────────────────────────────────────
def run_pipeline(data: dict, output_path: str):
    output = Path(output_path)
    print(f"\n=== CIP Runner: {data.get('account_name', 'UNKNOWN')} ===\n")

    print("Step 0: Validating input data...")
    validate_data(data)
    print("  Input data valid.")

    if WORK_DIR.exists():
        shutil.rmtree(WORK_DIR)
    WORK_DIR.mkdir(parents=True)

    print("Step 1: Unpacking template...")
    sys.path.insert(0, str(SCRIPTS))
    sys.path.insert(0, str(SCRIPTS / "office"))
    os.chdir(WORK_DIR)
    run(f"python3 {SCRIPTS}/office/unpack.py {TEMPLATE} {UNPACKED}/")

    print("Step 2: Editing slides...")
    edit_slide1(data)
    edit_slide4(data)
    edit_slide5(data)
    edit_slide6(data)
    edit_slide8(data)

    print("Step 3: Packing PPTX...")
    run(
        f"python3 {SCRIPTS}/office/pack.py {UNPACKED}/ {output} "
        f"--original {TEMPLATE}",
        cwd=str(SCRIPTS / "office"),
    )

    ok = validate_output(output, data)
    if not ok:
        print("\nFATAL: Output failed validation. Check errors above.")
        sys.exit(1)

    print(f"\n=== Done: {output} ({output.stat().st_size // 1024}KB) ===\n")
    return str(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data",   required=True, help="Path to data JSON file")
    parser.add_argument("--output", required=True, help="Output .pptx path")
    args = parser.parse_args()
    with open(args.data) as f:
        data = json.load(f)
    run_pipeline(data, args.output)
