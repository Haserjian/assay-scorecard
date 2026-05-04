# Methodology note: three-axis evidence-readiness split

**Date:** 2026-04-25
**Trigger:** DSPy / Khattab outreach (email 2026-04-22, no reply at +3d) surfaced an overloaded grading issue.
**Status:** backlog — do not act today; revisit after crash-test-lane outbound has reply data.

## What the current scorecard does

Grades a project on whether it emits independently verifiable evidence at the LLM call site (signed receipts, proof packs, CI gates, signing keys, equivalents). Single axis, single grade.

## Why that's overloaded

Detected absence of native verifier-grade artifacts is real, but collapsing it into a single grade conflates three distinct questions:

| Axis | Question | Failure mode if conflated |
|---|---|---|
| 1. Native verifier-grade evidence artifacts | Does the framework itself emit signed receipts / proof packs / verifiable artifacts at the call site? | Treats projects whose scope ≠ assurance as "failing" their job |
| 2. Instrumentation / callback hooks | Can a user attach callbacks, logging, tracing, or middleware to the call path? | Misses that the framework is integrable even if not assurance-native |
| 3. External observability / assurance compatibility | Does the framework cleanly compose with MLflow / Langfuse / OpenTelemetry / external assurance layers? | Conflates "not built for assurance" with "incompatible with assurance" |

## Concrete example: DSPy

DSPy publicly frames itself as a declarative framework for programming modular AI systems and optimizing prompts/weights — not as an assurance/runtime-evidence layer. Its observability tutorial points to debugging, MLflow tracing, and custom callbacks. MLflow's DSPy integration captures traces/metadata, but that is not the same as signed, independently verifiable call-site receipts.

Likely scores under three-axis split:

| Axis | DSPy |
|---|---|
| Native evidence artifacts | low |
| Instrumentation hooks | moderate / good |
| External observability compatibility | good (MLflow, custom callbacks) |

A single "F" on the current scorecard reads as a broad quality judgment. Under the three-axis split, the same finding reads as: *DSPy appears low on native verifier-grade call-site evidence emission; evidence-readiness likely requires an external assurance layer.* That's true and defensible, where the "F" framing is overconfident.

## Public claim to preserve under any revision

DSPy (and frameworks like it) **does not appear to natively emit verifier-grade call-site evidence artifacts.**

## Public claim to retire

DSPy (and frameworks like it) **deserves an F on evidence-readiness.**

## Reframe the scorecard with

Something like: *DSPy appears low on native verifier-grade call-site evidence emission; evidence-readiness for adopters likely requires an external assurance layer.*

## Action

- **Today (2026-04-25):** none. This is methodology backlog, not a same-day push.
- **Backlog:** revise `methodology.md` + `scan.py` + `build_site.py` to emit three sub-grades instead of one. Revise the per-repo report templates so the "F" is replaced with a tri-axis summary.
- **Khattab thread:** do not follow up. The original question ("am I wrong?") is answered. If he ever replies, this note is the basis for the cleaner response.
- **Doctrine corollary:** the scorecard should distinguish *not evidence-native* from *not instrumentable* in any future communications about scanned projects.

## Lane separation

This note is **scorecard methodology repair** lane.
It is **NOT** the customer-data-boundary crash-test outbound lane.
Do not let revising the scorecard bleed into "more building" inside the crash-test 10-sends operating rule.

## References

- `methodology.md` — current single-axis methodology this note proposes to revise.
- `site/reports/stanfordnlp_dspy.html` — example public report containing the "F" framing this note retires.
- DSPy docs — observability points to MLflow tracing + custom callbacks, not native evidence emission.
- This note triggered by the email Tim Haserjian → okhattab@stanford.edu, 2026-04-22 16:58 PT, no reply at +3d.
