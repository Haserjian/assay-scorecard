#!/usr/bin/env python3
"""
Scorecard scanner: clone repos, run assay scan + score, collect results.

Usage:
    python scan.py                    # scan all repos in repos.yaml
    python scan.py --limit 5          # scan first 5 only
    python scan.py --repo owner/name  # scan a single repo

Output:
    site/data/results.json            # combined results for the static site
    site/reports/<owner>_<repo>.html  # per-repo HTML reports
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import yaml


ASSAY_VERSION = "1.5.3"  # pinned — bump deliberately, not silently
RESULTS_DIR = Path("site/data")
REPORTS_DIR = Path("site/reports")
WORKDIR = Path("workdir")


def load_repos(path: str = "repos.yaml", limit: int | None = None) -> list[dict]:
    with open(path) as f:
        data = yaml.safe_load(f)
    targets = data.get("targets", [])
    if limit:
        targets = targets[:limit]
    return targets


def clone_repo(repo: str, dest: Path) -> bool:
    """Shallow clone default branch. Returns True on success."""
    url = f"https://github.com/{repo}.git"
    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", "--single-branch", url, str(dest)],
            check=True,
            capture_output=True,
            timeout=120,
        )
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        print(f"  CLONE FAILED: {repo} — {e}", file=sys.stderr)
        return False


def run_assay_scan(repo_dir: Path) -> dict | None:
    """Run `assay scan . --json` and return parsed JSON."""
    try:
        result = subprocess.run(
            ["assay", "scan", ".", "--json"],
            cwd=str(repo_dir),
            capture_output=True,
            text=True,
            timeout=300,
        )
        # assay scan returns exit 0 on pass, 1 on fail (uninstrumented sites found)
        # both are valid — we want the JSON either way
        if result.stdout.strip():
            return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError) as e:
        print(f"  SCAN FAILED: {e}", file=sys.stderr)
    return None


def run_assay_score(repo_dir: Path) -> dict | None:
    """Run `assay score . --json` and return parsed JSON."""
    try:
        result = subprocess.run(
            ["assay", "score", ".", "--json"],
            cwd=str(repo_dir),
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.stdout.strip():
            return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError) as e:
        print(f"  SCORE FAILED: {e}", file=sys.stderr)
    return None


def run_assay_report(repo_dir: Path, output_path: Path) -> bool:
    """Run `assay scan . --report` and copy the HTML report."""
    try:
        subprocess.run(
            ["assay", "scan", ".", "--report"],
            cwd=str(repo_dir),
            capture_output=True,
            text=True,
            timeout=300,
        )
        # Default output location
        report_src = repo_dir / "evidence_gap_report.html"
        if report_src.exists():
            shutil.copy2(report_src, output_path)
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"  REPORT FAILED: {e}", file=sys.stderr)
    return False


def get_github_stars(repo: str) -> int | None:
    """Fetch star count via gh CLI."""
    try:
        result = subprocess.run(
            ["gh", "api", f"repos/{repo}", "--jq", ".stargazers_count"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0 and result.stdout.strip():
            return int(result.stdout.strip())
    except (subprocess.TimeoutExpired, ValueError):
        pass
    return None


def scan_repo(target: dict) -> dict:
    """Scan a single repo and return its result entry."""
    repo = target["repo"]
    category = target.get("category", "unknown")
    print(f"Scanning {repo}...")

    entry = {
        "repo": repo,
        "category": category,
        "scanned_at": datetime.now(timezone.utc).isoformat(),
        "stars": None,
        "scan": None,
        "score": None,
        "report_path": None,
        "error": None,
    }

    # Get stars
    entry["stars"] = get_github_stars(repo)

    # Clone
    clone_dir = WORKDIR / repo.replace("/", "_")
    if clone_dir.exists():
        shutil.rmtree(clone_dir)

    if not clone_repo(repo, clone_dir):
        entry["error"] = "clone_failed"
        return entry

    # Scan
    scan_result = run_assay_scan(clone_dir)
    if scan_result:
        entry["scan"] = {
            "sites_total": scan_result.get("summary", {}).get("sites_total", 0),
            "instrumented": scan_result.get("summary", {}).get("instrumented", 0),
            "uninstrumented": scan_result.get("summary", {}).get("uninstrumented", 0),
            "scan_status": scan_result.get("scan_status", "unknown"),
        }

    # Score
    score_result = run_assay_score(clone_dir)
    if score_result:
        entry["score"] = {
            "score": score_result.get("score", 0),
            "grade": score_result.get("grade", "F"),
            "breakdown": score_result.get("breakdown", {}),
        }

    # HTML report
    report_name = repo.replace("/", "_") + ".html"
    report_path = REPORTS_DIR / report_name
    if run_assay_report(clone_dir, report_path):
        entry["report_path"] = f"reports/{report_name}"

    # Cleanup clone
    shutil.rmtree(clone_dir, ignore_errors=True)

    status = "ok" if scan_result else "scan_failed"
    print(f"  {repo}: {status}")
    return entry


def main():
    parser = argparse.ArgumentParser(description="Assay Evidence Readiness Scorecard scanner")
    parser.add_argument("--limit", type=int, help="Scan only first N repos")
    parser.add_argument("--repo", type=str, help="Scan a single repo (owner/name)")
    args = parser.parse_args()

    # Ensure output dirs exist
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    WORKDIR.mkdir(parents=True, exist_ok=True)

    if args.repo:
        targets = [{"repo": args.repo, "category": "manual"}]
    else:
        targets = load_repos(limit=args.limit)

    print(f"Scanning {len(targets)} repos (assay-ai pinned to {ASSAY_VERSION})...")
    print()

    results = []
    for target in targets:
        try:
            entry = scan_repo(target)
        except Exception as e:
            print(f"  UNEXPECTED ERROR scanning {target.get('repo', '?')}: {e}", file=sys.stderr)
            entry = {
                "repo": target.get("repo", "unknown"),
                "category": target.get("category", "unknown"),
                "scanned_at": datetime.now(timezone.utc).isoformat(),
                "stars": None,
                "scan": None,
                "score": None,
                "report_path": None,
                "error": f"unexpected: {e}",
            }
        results.append(entry)

    # Write combined results
    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "assay_version": ASSAY_VERSION,
        "repo_count": len(results),
        "results": results,
    }
    output_path = RESULTS_DIR / "results.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print()
    print(f"Results written to {output_path}")
    print(f"Reports in {REPORTS_DIR}/")

    # Summary
    ok = sum(1 for r in results if r.get("scan") is not None)
    failed = len(results) - ok
    print(f"Success: {ok}/{len(results)}  Failed: {failed}")


if __name__ == "__main__":
    main()
