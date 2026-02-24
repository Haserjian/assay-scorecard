#!/usr/bin/env python3
"""Compute Evidence Readiness Score delta between base and head revisions.

Designed for PR workflows: compares scan/score output from two revisions
and produces a delta report (JSON + markdown).

Usage:
    python scripts/pr_score_delta.py --base-json base.json --head-json head.json
    python scripts/pr_score_delta.py --base-json base.json --head-json head.json --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


def load_scan_score(path: Path) -> Dict[str, Any]:
    """Load a combined scan+score JSON file."""
    with open(path) as f:
        return json.load(f)


def compute_delta(base: Dict[str, Any], head: Dict[str, Any]) -> Dict[str, Any]:
    """Compute delta between base and head scan/score results.

    Args:
        base: Scan/score JSON from base revision
        head: Scan/score JSON from head revision

    Returns:
        Delta dict with before/after/change for each metric.
    """
    base_scan = base.get("scan", {}).get("summary", base.get("scan", {}))
    head_scan = head.get("scan", {}).get("summary", head.get("scan", {}))

    base_score = base.get("score", {})
    head_score = head.get("score", {})

    b_sites = base_scan.get("sites_total", 0)
    h_sites = head_scan.get("sites_total", 0)
    b_instr = base_scan.get("instrumented", 0)
    h_instr = head_scan.get("instrumented", 0)
    b_uninstr = base_scan.get("uninstrumented", 0)
    h_uninstr = head_scan.get("uninstrumented", 0)
    b_score_val = base_score.get("score", 0)
    h_score_val = head_score.get("score", 0)
    b_grade = base_score.get("grade", "?")
    h_grade = head_score.get("grade", "?")

    return {
        "sites_total": {"base": b_sites, "head": h_sites, "delta": h_sites - b_sites},
        "instrumented": {"base": b_instr, "head": h_instr, "delta": h_instr - b_instr},
        "uninstrumented": {"base": b_uninstr, "head": h_uninstr, "delta": h_uninstr - b_uninstr},
        "score": {"base": b_score_val, "head": h_score_val, "delta": round(h_score_val - b_score_val, 1)},
        "grade": {"base": b_grade, "head": h_grade},
        "coverage_pct": {
            "base": round(b_instr / b_sites * 100, 1) if b_sites > 0 else 0,
            "head": round(h_instr / h_sites * 100, 1) if h_sites > 0 else 0,
        },
    }


def find_new_uninstrumented(base: Dict[str, Any], head: Dict[str, Any]) -> List[Dict[str, str]]:
    """Find call sites that are in head but not in base (new uninstrumented sites).

    Falls back to empty list if detailed site data isn't available.
    """
    base_sites = set()
    head_new = []

    # Extract site identifiers from scan results
    for site in base.get("scan", {}).get("sites", base.get("sites", [])):
        key = f"{site.get('file', '')}:{site.get('line', '')}:{site.get('call', '')}"
        base_sites.add(key)

    for site in head.get("scan", {}).get("sites", head.get("sites", [])):
        if not site.get("instrumented", False):
            key = f"{site.get('file', '')}:{site.get('line', '')}:{site.get('call', '')}"
            if key not in base_sites:
                head_new.append({
                    "file": site.get("file", "unknown"),
                    "line": str(site.get("line", "?")),
                    "call": site.get("call", "unknown"),
                    "provider": site.get("provider", "unknown"),
                })

    return head_new[:10]  # Cap at 10 for readability


def format_delta_icon(value: float, invert: bool = False) -> str:
    """Return a text icon for positive/negative/zero delta."""
    if value > 0:
        return "+" if not invert else "-"
    elif value < 0:
        return "-" if not invert else "+"
    return "="


def render_markdown(delta: Dict[str, Any], new_sites: List[Dict[str, str]]) -> str:
    """Render delta as a markdown PR comment."""
    lines = []
    lines.append("## Evidence Readiness Score Delta")
    lines.append("")

    score_d = delta["score"]
    score_icon = ""
    if score_d["delta"] > 0:
        score_icon = " [improved]"
    elif score_d["delta"] < 0:
        score_icon = " [regressed]"

    lines.append("| Metric | Base | Head | Delta |")
    lines.append("|--------|------|------|-------|")

    s = delta["score"]
    lines.append(f"| **Score** | {s['base']:.1f} | {s['head']:.1f} | {s['delta']:+.1f}{score_icon} |")

    g = delta["grade"]
    grade_change = f"{g['base']} -> {g['head']}" if g['base'] != g['head'] else g['head']
    lines.append(f"| **Grade** | {g['base']} | {g['head']} | {grade_change} |")

    st = delta["sites_total"]
    lines.append(f"| Call Sites | {st['base']} | {st['head']} | {st['delta']:+d} |")

    inst = delta["instrumented"]
    lines.append(f"| Instrumented | {inst['base']} | {inst['head']} | {inst['delta']:+d} |")

    uninst = delta["uninstrumented"]
    lines.append(f"| Uninstrumented | {uninst['base']} | {uninst['head']} | {uninst['delta']:+d} |")

    cov = delta["coverage_pct"]
    cov_delta = cov["head"] - cov["base"]
    lines.append(f"| Coverage | {cov['base']:.1f}% | {cov['head']:.1f}% | {cov_delta:+.1f}% |")

    if new_sites:
        lines.append("")
        lines.append("### New Uninstrumented Call Sites")
        lines.append("")
        lines.append("| File | Line | Call | Provider |")
        lines.append("|------|------|------|----------|")
        for site in new_sites:
            lines.append(f"| `{site['file']}` | {site['line']} | `{site['call']}` | {site['provider']} |")
        lines.append("")
        lines.append("> Fix: `pip install assay-ai && assay patch .` to auto-instrument these sites.")

    lines.append("")
    lines.append("---")
    lines.append("*Generated by [Assay Scorecard](https://haserjian.github.io/assay-scorecard/) | [Methodology](https://haserjian.github.io/assay-scorecard/methodology.html)*")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Compute Evidence Readiness Score delta")
    parser.add_argument("--base-json", required=True, help="Path to base revision scan/score JSON")
    parser.add_argument("--head-json", required=True, help="Path to head revision scan/score JSON")
    parser.add_argument("--output", help="Output file for markdown (default: stdout)")
    parser.add_argument("--json", dest="json_output", action="store_true", help="Output as JSON instead of markdown")
    parser.add_argument("--fail-on-regression", action="store_true", help="Exit 1 if score decreased")
    args = parser.parse_args()

    base_path = Path(args.base_json)
    head_path = Path(args.head_json)

    if not base_path.exists():
        print(f"Error: base file not found: {base_path}", file=sys.stderr)
        sys.exit(3)
    if not head_path.exists():
        print(f"Error: head file not found: {head_path}", file=sys.stderr)
        sys.exit(3)

    try:
        base = load_scan_score(base_path)
        head = load_scan_score(head_path)
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error: failed to parse input: {e}", file=sys.stderr)
        sys.exit(3)

    delta = compute_delta(base, head)
    new_sites = find_new_uninstrumented(base, head)

    if args.json_output:
        output = {
            "delta": delta,
            "new_uninstrumented_sites": new_sites,
            "regressed": delta["score"]["delta"] < 0,
        }
        result = json.dumps(output, indent=2)
    else:
        result = render_markdown(delta, new_sites)

    if args.output:
        Path(args.output).write_text(result)
    else:
        print(result)

    if args.fail_on_regression and delta["score"]["delta"] < 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
