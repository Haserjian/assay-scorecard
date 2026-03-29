# Assay Evidence Readiness Scorecard

Weekly automated scan of 20 popular AI/ML repositories measuring
how much of their LLM-calling behavior is independently verifiable
through tamper-evident audit trails.

**Current result: all 20 repositories score F.**

None of the scanned projects have receipt-based evidence infrastructure
for their LLM calls. That means evaluation claims, benchmark results,
and model-improvement deltas from these projects cannot be independently
verified or audited after the fact.

## Why this matters

When an AI system calls an LLM, the inputs, outputs, model version,
and parameters are ephemeral by default. Without evidence infrastructure:

- Eval improvements may reflect judge drift, not real gains
- Benchmark claims cannot be audited after publication
- Compliance teams cannot prove what the AI actually did
- Incidents cannot be replayed from evidence

The scorecard measures readiness for this kind of auditability.

## What we scan

20 high-profile AI repositories including AutoGPT, LangChain, MetaGPT,
CrewAI, DSPy, LiteLLM, Pydantic-AI, and others. Full list in
[repos.yaml](repos.yaml).

Scanning uses [assay-ai](https://pypi.org/project/assay-ai/) v1.19.0
for AST-based detection of LLM call sites across OpenAI, Anthropic,
Google Gemini, LangChain, and LiteLLM SDKs.

## Score components

| Component | Weight | What it checks |
|-----------|--------|----------------|
| Coverage | 35% | Instrumented vs total LLM call sites |
| Lockfile | 15% | `assay.lock` present and valid |
| CI Gate | 20% | CI workflow referencing assay commands |
| Receipts | 20% | Proof pack receipt files in repo |
| Key Setup | 10% | Signing key configured |

Grades: A (90+), B (80+), C (70+), D (60+), F (<60).
Zero receipts caps at grade D regardless of other scores.

## Check your own repo

```bash
pip install assay-ai
cd your-repo
assay scan .
assay score .
```

## Methodology

See [methodology.md](methodology.md) for full details including known
limitations, scanning approach, and correction/appeal process.

## Related

- [Assay](https://github.com/Haserjian/assay) — the evidence compiler
- [Proof Gallery](https://github.com/Haserjian/assay-proof-gallery) — demo artifacts + browser verifier
- [Assay Verify Action](https://github.com/Haserjian/assay-verify-action) — GitHub Actions CI gate

## Live scorecard

[View the scorecard](https://haserjian.github.io/assay-scorecard/)
