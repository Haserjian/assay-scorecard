#!/usr/bin/env python3
"""
Build static scorecard site from scan results.

Reads:  site/data/results.json
Writes: site/index.html, site/sitemap.xml, site/robots.txt
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

SITE_DIR = Path("site")
DATA_FILE = SITE_DIR / "data" / "results.json"
SITE_URL = "https://haserjian.github.io/assay-scorecard"


def grade_color(grade: str) -> str:
    return {
        "A": "#22c55e",
        "B": "#84cc16",
        "C": "#eab308",
        "D": "#f97316",
        "F": "#ef4444",
    }.get(grade, "#6b7280")


def grade_bg(grade: str) -> str:
    return {
        "A": "#052e16",
        "B": "#1a2e05",
        "C": "#2e2505",
        "D": "#2e1505",
        "F": "#2e0505",
    }.get(grade, "#1f2937")


def build_row(r: dict) -> str:
    repo = r["repo"]
    stars = r.get("stars") or 0
    scan = r.get("scan") or {}
    score_data = r.get("score") or {}

    sites = scan.get("sites_total", 0)
    instrumented = scan.get("instrumented", 0)
    uninstrumented = scan.get("uninstrumented", 0)

    score = score_data.get("score", 0)
    grade = score_data.get("grade", "?")
    color = grade_color(grade)
    bg = grade_bg(grade)

    report_link = ""
    if r.get("report_path"):
        report_link = f'<a href="{r["report_path"]}" class="report-link">View Report</a>'

    coverage_pct = f"{instrumented}/{sites}" if sites > 0 else "0/0"

    stars_display = f"{stars:,}" if stars else "?"

    return f"""<tr>
      <td><a href="https://github.com/{repo}" target="_blank" rel="noopener">{repo}</a></td>
      <td class="num">{stars_display}</td>
      <td class="num">{sites}</td>
      <td class="num">{coverage_pct}</td>
      <td class="num"><span class="grade" style="background:{bg};color:{color}">{grade}</span> {score:.0f}</td>
      <td>{report_link}</td>
    </tr>"""


def build_html(data: dict) -> str:
    results = sorted(
        data.get("results", []),
        key=lambda r: r.get("repo", "").lower(),
    )
    generated = data.get("generated_at", "unknown")
    assay_ver = data.get("assay_version", "unknown")
    count = len(results)

    rows = "\n".join(build_row(r) for r in results)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI Evidence Readiness Scorecard</title>
  <meta name="description" content="How much of your AI system's behavior is independently verifiable? Evidence readiness scores for top AI repositories.">

  <!-- Open Graph -->
  <meta property="og:title" content="AI Evidence Readiness Scorecard">
  <meta property="og:description" content="Evidence readiness scores for {count} top AI repositories. How much is verifiable?">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{SITE_URL}">

  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary">
  <meta name="twitter:title" content="AI Evidence Readiness Scorecard">
  <meta name="twitter:description" content="We scanned {count} top AI repos for tamper-evident audit trails. Evidence readiness scores for LangChain, crewAI, AutoGPT, and more.">

  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}

    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: #0d1117;
      color: #c9d1d9;
      line-height: 1.6;
    }}

    .container {{
      max-width: 1100px;
      margin: 0 auto;
      padding: 2rem 1rem;
    }}

    h1 {{
      font-size: 1.75rem;
      color: #f0f6fc;
      margin-bottom: 0.5rem;
    }}

    .subtitle {{
      color: #8b949e;
      margin-bottom: 2rem;
      font-size: 1rem;
    }}

    .meta {{
      color: #6e7681;
      font-size: 0.8rem;
      margin-bottom: 1.5rem;
    }}

    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.9rem;
    }}

    th {{
      text-align: left;
      padding: 0.75rem 0.5rem;
      border-bottom: 2px solid #30363d;
      color: #8b949e;
      font-weight: 600;
      font-size: 0.8rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      cursor: pointer;
      user-select: none;
    }}

    th:hover {{ color: #f0f6fc; }}

    td {{
      padding: 0.6rem 0.5rem;
      border-bottom: 1px solid #21262d;
    }}

    tr:hover {{ background: #161b22; }}

    .num {{ text-align: right; font-variant-numeric: tabular-nums; }}

    .grade {{
      display: inline-block;
      padding: 0.15rem 0.5rem;
      border-radius: 4px;
      font-weight: 700;
      font-size: 0.85rem;
      min-width: 1.5rem;
      text-align: center;
    }}

    a {{ color: #58a6ff; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}

    .report-link {{
      font-size: 0.8rem;
      color: #8b949e;
    }}
    .report-link:hover {{ color: #58a6ff; }}

    .cta {{
      margin-top: 2rem;
      padding: 1.25rem;
      background: #161b22;
      border: 1px solid #30363d;
      border-radius: 8px;
    }}

    .cta code {{
      background: #0d1117;
      padding: 0.2rem 0.4rem;
      border-radius: 4px;
      font-size: 0.85rem;
    }}

    .footer {{
      margin-top: 3rem;
      padding-top: 1rem;
      border-top: 1px solid #21262d;
      color: #6e7681;
      font-size: 0.8rem;
    }}

    .footer a {{ color: #6e7681; }}
  </style>
</head>
<body>
  <div class="container">
    <h1>AI Evidence Readiness Scorecard</h1>
    <p class="subtitle">How much of your AI system's behavior is independently verifiable?</p>

    <p style="color:#d29922; font-size:0.85rem; background:#2e2505; border:1px solid #d29922; border-radius:6px; padding:0.6rem 1rem; margin-bottom:1.25rem;">
      <strong>Beta.</strong> This scorecard measures evidence readiness (instrumentation coverage), not project quality.
      Most AI projects score low because tamper-evident audit trails are new.
      <a href="methodology.html" style="color:#d29922;">Methodology</a>
    </p>

    <p class="meta">
      {count} repos scanned with <a href="https://pypi.org/project/assay-ai/">assay-ai</a> v{assay_ver}
      &middot; Last updated: {generated[:10]}
      &middot; <a href="methodology.html">How we score</a>
    </p>

    <table id="scorecard">
      <thead>
        <tr>
          <th onclick="sortTable(0)">Repository</th>
          <th onclick="sortTable(1)">Stars</th>
          <th onclick="sortTable(2)">Call Sites</th>
          <th onclick="sortTable(3)">Instrumented</th>
          <th onclick="sortTable(4)">Score</th>
          <th>Report</th>
        </tr>
      </thead>
      <tbody>
        {rows}
      </tbody>
    </table>

    <div class="cta">
      <strong>Check your own repo:</strong><br>
      <code>pip install assay-ai && assay scan . && assay score .</code>
    </div>

    <div class="footer">
      <p>
        <a href="https://github.com/Haserjian/assay-scorecard">Source</a>
        &middot; <a href="methodology.html">Methodology</a>
        &middot; <a href="https://github.com/Haserjian/assay-scorecard/issues">Report an issue</a>
        &middot; Powered by <a href="https://pypi.org/project/assay-ai/">Assay</a>
      </p>
    </div>
  </div>

  <script>
    function sortTable(col) {{
      const table = document.getElementById('scorecard');
      const tbody = table.querySelector('tbody');
      const rows = Array.from(tbody.querySelectorAll('tr'));
      const dir = table.dataset.sortDir === 'asc' ? 'desc' : 'asc';
      table.dataset.sortDir = dir;

      rows.sort((a, b) => {{
        let av = a.cells[col].textContent.trim().replace(/,/g, '');
        let bv = b.cells[col].textContent.trim().replace(/,/g, '');
        const an = parseFloat(av), bn = parseFloat(bv);
        if (!isNaN(an) && !isNaN(bn)) {{
          return dir === 'asc' ? an - bn : bn - an;
        }}
        return dir === 'asc' ? av.localeCompare(bv) : bv.localeCompare(av);
      }});

      rows.forEach(r => tbody.appendChild(r));
    }}
  </script>
</body>
</html>"""


def build_sitemap(data: dict) -> str:
    urls = [f"  <url><loc>{SITE_URL}/</loc></url>"]
    urls.append(f"  <url><loc>{SITE_URL}/methodology.html</loc></url>")
    for r in data.get("results", []):
        if r.get("report_path"):
            urls.append(f"  <url><loc>{SITE_URL}/{r['report_path']}</loc></url>")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(urls)}
</urlset>"""


def main():
    if not DATA_FILE.exists():
        print(f"No results file at {DATA_FILE}. Run scan.py first.")
        return

    with open(DATA_FILE) as f:
        data = json.load(f)

    # Build index.html
    html = build_html(data)
    index_path = SITE_DIR / "index.html"
    index_path.write_text(html)
    print(f"Built {index_path}")

    # Copy methodology
    methodology_src = Path("methodology.md")
    if methodology_src.exists():
        # Simple markdown -> html wrapper
        content = methodology_src.read_text()
        meth_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Scoring Methodology - AI Evidence Readiness Scorecard</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; background: #0d1117; color: #c9d1d9; line-height: 1.8; max-width: 720px; margin: 0 auto; padding: 2rem 1rem; }}
    h1, h2, h3 {{ color: #f0f6fc; }}
    a {{ color: #58a6ff; }}
    code {{ background: #161b22; padding: 0.15rem 0.35rem; border-radius: 4px; font-size: 0.9rem; }}
    pre {{ background: #161b22; padding: 1rem; border-radius: 8px; overflow-x: auto; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ padding: 0.5rem; border-bottom: 1px solid #30363d; text-align: left; }}
    th {{ color: #8b949e; }}
  </style>
</head>
<body>
  <p><a href="index.html">&larr; Back to Scorecard</a></p>
  <pre style="white-space: pre-wrap;">{content}</pre>
</body>
</html>"""
        meth_path = SITE_DIR / "methodology.html"
        meth_path.write_text(meth_html)
        print(f"Built {meth_path}")

    # Sitemap
    sitemap = build_sitemap(data)
    sitemap_path = SITE_DIR / "sitemap.xml"
    sitemap_path.write_text(sitemap)
    print(f"Built {sitemap_path}")

    # Robots.txt
    robots = f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n"
    robots_path = SITE_DIR / "robots.txt"
    robots_path.write_text(robots)
    print(f"Built {robots_path}")


if __name__ == "__main__":
    main()
