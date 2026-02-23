# How We Score

> **Beta.** This scorecard is an early, automated signal — not a final verdict.
> Scores reflect static analysis of public default branches using
> [Assay](https://pypi.org/project/assay-ai/) v1.6.0. Known limitations are
> listed below. If a result looks wrong, [open an issue](https://github.com/Haserjian/assay-scorecard/issues)
> and we will investigate within 48 hours or remove the entry on request.

## What This Is

The Assay Evidence Readiness Scorecard measures how much of an AI project's
LLM-calling behavior is independently verifiable. It is **not** a security
audit, vulnerability scan, or quality assessment.

## What We Scan

We use [Assay](https://pypi.org/project/assay-ai/) to detect LLM API call
sites in Python source code via AST analysis. Detected SDKs:

- OpenAI (`openai`)
- Anthropic (`anthropic`)
- Google Gemini (`google.generativeai`)
- LangChain (`langchain`)
- LiteLLM (`litellm`)

## Evidence Readiness Score (0-100)

The score is a weighted composite of 5 components:

| Component | Weight | What it checks |
|-----------|--------|----------------|
| Coverage | 35% | Ratio of instrumented to total LLM call sites |
| Lockfile | 15% | `assay.lock` present and valid |
| CI Gate | 20% | CI workflow referencing assay commands |
| Receipts | 20% | Proof pack receipt files in repo |
| Key Setup | 10% | Signing key configured |

Grades: A (90+), B (80+), C (70+), D (60+), F (<60)

**Anti-gaming:** Projects with zero receipts are capped at grade D regardless
of other scores.

## Known Limitations

- **Python only.** We don't scan TypeScript, Go, Rust, or other languages.
- **AST-based.** Dynamic call construction (e.g., `getattr(module, "create")`)
  may be missed.
- **Framework callbacks.** LangChain and LiteLLM callbacks are excluded from
  the call site count (they lack a direct stack frame).
- **Monorepo noise.** Large monorepos may have call sites in examples/tests
  that inflate the count.
- **Score reflects readiness, not security.** A high score means evidence
  infrastructure is in place, not that the system is "safe."

## Scanning is Non-Invasive

- We clone the default branch only (read-only)
- We do not execute any code in the scanned repository
- We do not access APIs, secrets, or runtime environments
- We do not modify the repository in any way
- Scan results are generated from static AST analysis only

## Corrections and Appeals

If you believe a scan result is inaccurate:

1. **False positive:** Open an issue in this repo with the repo name and the
   specific finding. We will investigate and fix within 48 hours.
2. **Missing context:** If your project instruments LLM calls through a
   mechanism Assay doesn't detect, let us know and we'll update the scanner.
3. **Opt-out:** If you want your repo removed from the scorecard, open an
   issue. We will remove it, no questions asked.

## Scan Frequency

Scans run weekly (Sunday night UTC). Results reflect the default branch
at scan time.

## Open Source

The scanner ([assay-ai](https://pypi.org/project/assay-ai/)) and this
scorecard pipeline are open source. You can verify any result:

```bash
pip install assay-ai
git clone https://github.com/<owner>/<repo>
cd <repo>
assay scan . --json
assay score . --json
```
