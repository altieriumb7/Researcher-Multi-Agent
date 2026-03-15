# Milestone 6 Readiness: Weakness Assessment

This note captures the highest-risk gaps observed in the current implementation before declaring Milestone 6 complete.

## 1) Five weakest parts of the current system

1. **No real model/tool runtime integration (deterministic-only behavior).**
   - The whole orchestration currently instantiates deterministic local agents and validates handcrafted payloads rather than invoking real LLM responses or external tools.
   - This is excellent for scaffolding/tests, but it does not exercise real-world nondeterminism, latency, API errors, or prompt drift.

2. **No actual revision loop despite review gates.**
   - Stage review gates can return `REVISE`/`REJECT`, but the engine only blocks downstream delegates and does not re-plan/re-run a corrected stage.
   - The current flow therefore behaves like a one-shot pipeline with stop conditions, not an iterative research workflow.

3. **State model is weakly typed at storage boundaries.**
   - Shared state stores most artifacts as `list[dict[str, Any]]`, and chief state updates can overwrite list fields directly.
   - This weak typing makes silent shape drift and backward-incompatible state payloads likely once multiple clients/services write state.

4. **Schema validation is presence- and literal-centric, not semantic.**
   - Validation heavily checks required fields and enum-like literals, but many nested values are not type/range/consistency constrained in depth.
   - Invalid but syntactically complete outputs can still pass and propagate into downstream logic.

5. **Validation suite is strong for unit behavior but thin for production failure modes.**
   - Tests cover routing, schema failures, dependency skips, and gate blocking, but there is no coverage for concurrency, retries, idempotency, persistence failures, model timeouts, or recovery after partial completion.

## 2) Architectural vs test-related classification

- **Architectural weaknesses:**
  1. Deterministic-only runtime (no real provider/tool execution path)
  2. Missing revision loop implementation
  3. Weakly typed state storage and permissive state mutation
  4. Limited semantic validation depth

- **Primarily test-related weakness:**
  5. Missing production-grade reliability/integration test scenarios (timeouts, retries, persistence/restart, etc.)

## 3) What would likely break first in production usage

Most likely first failure: **outputs from a real LLM would violate current strict/flat schema assumptions**, causing frequent validation errors or inconsistent state writes before useful end-to-end results are produced.

Why this is first:
- A live model introduces formatting variability immediately.
- There is no retry/repair layer for invalid outputs.
- Review gates block but do not execute remediation cycles.
- State writes accept broad dict/list payloads, so near-valid artifacts may still create brittle downstream behavior.

## 4) What I would improve next in one additional milestone

If granted one more milestone, I would prioritize **"Milestone 7: Production Hardening"** with this order:

1. **Introduce resilient agent execution adapters**
   - Real model client abstraction with structured-output retry, backoff, timeout handling, and response normalization.

2. **Implement true revise/replan loops**
   - On `REVISE`, feed reviewer instructions back to the stage owner (or chief) and cap attempts with clear stop conditions.

3. **Strengthen typed state boundaries**
   - Replace raw list/dict storage with typed envelope objects + versioning for state artifacts.

4. **Add end-to-end fault-injection tests**
   - Simulate invalid model output, transient failures, and resume-after-failure behavior.

5. **Add observability contracts**
   - Standardized event schema + correlation IDs for every stage/review to support debugging and operational monitoring.
