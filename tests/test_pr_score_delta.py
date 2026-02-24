"""Tests for PR score delta computation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

# Import from scripts directory
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from pr_score_delta import compute_delta, find_new_uninstrumented, render_markdown


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _scan_score(sites_total=10, instrumented=5, uninstrumented=5, score=17.5, grade="F", sites=None):
    """Build a mock scan+score result."""
    result = {
        "scan": {
            "summary": {
                "sites_total": sites_total,
                "instrumented": instrumented,
                "uninstrumented": uninstrumented,
            },
            "sites": sites or [],
        },
        "score": {
            "score": score,
            "grade": grade,
        },
    }
    return result


def _site(file="app.py", line=42, call="client.chat.completions.create", provider="openai", instrumented=False):
    return {"file": file, "line": line, "call": call, "provider": provider, "instrumented": instrumented}


# ---------------------------------------------------------------------------
# Test: compute_delta
# ---------------------------------------------------------------------------

class TestComputeDelta:
    def test_no_change(self):
        base = _scan_score()
        head = _scan_score()
        delta = compute_delta(base, head)
        assert delta["score"]["delta"] == 0
        assert delta["sites_total"]["delta"] == 0
        assert delta["instrumented"]["delta"] == 0

    def test_score_improved(self):
        base = _scan_score(score=10.0, grade="F")
        head = _scan_score(score=25.0, grade="F")
        delta = compute_delta(base, head)
        assert delta["score"]["delta"] == 15.0
        assert delta["score"]["head"] == 25.0

    def test_score_regressed(self):
        base = _scan_score(score=25.0, grade="F")
        head = _scan_score(score=10.0, grade="F")
        delta = compute_delta(base, head)
        assert delta["score"]["delta"] == -15.0

    def test_new_call_sites(self):
        base = _scan_score(sites_total=10, uninstrumented=5)
        head = _scan_score(sites_total=15, uninstrumented=10)
        delta = compute_delta(base, head)
        assert delta["sites_total"]["delta"] == 5
        assert delta["uninstrumented"]["delta"] == 5

    def test_coverage_pct(self):
        base = _scan_score(sites_total=10, instrumented=5)
        head = _scan_score(sites_total=10, instrumented=8)
        delta = compute_delta(base, head)
        assert delta["coverage_pct"]["base"] == 50.0
        assert delta["coverage_pct"]["head"] == 80.0

    def test_zero_sites(self):
        base = _scan_score(sites_total=0, instrumented=0, uninstrumented=0)
        head = _scan_score(sites_total=5, instrumented=0, uninstrumented=5)
        delta = compute_delta(base, head)
        assert delta["coverage_pct"]["base"] == 0
        assert delta["sites_total"]["delta"] == 5

    def test_grade_change(self):
        base = _scan_score(score=55.0, grade="F")
        head = _scan_score(score=75.0, grade="C")
        delta = compute_delta(base, head)
        assert delta["grade"]["base"] == "F"
        assert delta["grade"]["head"] == "C"


# ---------------------------------------------------------------------------
# Test: find_new_uninstrumented
# ---------------------------------------------------------------------------

class TestFindNewUninstrumented:
    def test_no_new_sites(self):
        site = _site()
        base = _scan_score(sites=[site])
        head = _scan_score(sites=[site])
        new = find_new_uninstrumented(base, head)
        assert len(new) == 0

    def test_new_uninstrumented_site(self):
        base = _scan_score(sites=[])
        head = _scan_score(sites=[_site(file="new.py", line=10)])
        new = find_new_uninstrumented(base, head)
        assert len(new) == 1
        assert new[0]["file"] == "new.py"

    def test_instrumented_sites_excluded(self):
        base = _scan_score(sites=[])
        head = _scan_score(sites=[_site(instrumented=True)])
        new = find_new_uninstrumented(base, head)
        assert len(new) == 0

    def test_capped_at_10(self):
        sites = [_site(file=f"f{i}.py", line=i) for i in range(20)]
        base = _scan_score(sites=[])
        head = _scan_score(sites=sites)
        new = find_new_uninstrumented(base, head)
        assert len(new) == 10

    def test_empty_scan_data(self):
        base = {"scan": {}, "score": {}}
        head = {"scan": {}, "score": {}}
        new = find_new_uninstrumented(base, head)
        assert new == []


# ---------------------------------------------------------------------------
# Test: render_markdown
# ---------------------------------------------------------------------------

class TestRenderMarkdown:
    def test_renders_table(self):
        delta = compute_delta(_scan_score(), _scan_score(score=20.0))
        md = render_markdown(delta, [])
        assert "Evidence Readiness Score Delta" in md
        assert "| Metric |" in md
        assert "| **Score** |" in md

    def test_renders_new_sites(self):
        delta = compute_delta(_scan_score(), _scan_score())
        sites = [{"file": "app.py", "line": "42", "call": "create", "provider": "openai"}]
        md = render_markdown(delta, sites)
        assert "New Uninstrumented Call Sites" in md
        assert "app.py" in md
        assert "assay patch" in md

    def test_regression_label(self):
        delta = compute_delta(_scan_score(score=20.0), _scan_score(score=10.0))
        md = render_markdown(delta, [])
        assert "regressed" in md

    def test_improvement_label(self):
        delta = compute_delta(_scan_score(score=10.0), _scan_score(score=20.0))
        md = render_markdown(delta, [])
        assert "improved" in md

    def test_no_label_on_zero_delta(self):
        delta = compute_delta(_scan_score(), _scan_score())
        md = render_markdown(delta, [])
        assert "regressed" not in md
        assert "improved" not in md

    def test_methodology_link(self):
        delta = compute_delta(_scan_score(), _scan_score())
        md = render_markdown(delta, [])
        assert "methodology.html" in md
