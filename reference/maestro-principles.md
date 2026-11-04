# Maestro principles

Read this before proposing any candidate system. Every candidate in Phase 2 and the final design
must answer each point. If a point does not apply, say why in one line rather than skipping it.

Source: github.com/stevencallaway1/maestro-ceo-scheduling (README and EXECUTIVE-SUMMARY).

## 1. Reframe the process as a judgment
What decision is this process really making, and why has it stayed with a human? The answer is
usually trust, not capability. Name the judgment in one sentence. A system that only automates the
mechanical part leaves the bottleneck in place.

## 2. Stages in order, each with one kind
Four to eight stages. Each is exactly one of: deterministic, model-backed (one call), human
decision point, external adapter. Intake never decides. Context (the dossier) is its own stage so
that flags come from assembled context rather than from surface text of the request.

## 3. Policy sets the outcome, not the model
Rules live in data, in plain English, editable by the process owner without an engineer. The
model writes about the outcome; it does not choose it. A model cannot talk its way past a rule.

## 4. The model cannot invent a resource
Any search for a legal option (a time slot, a vendor, an approver, a document, a budget line) runs
in deterministic code before the model call. The model only writes about that list.

## 5. Model-call cap as a number, with a zero path
State the maximum model calls per run. State the path where the count is zero: sensitive
categories stop at the policy stage and never reach a model, so they are never summarized or
paraphrased by one.

## 6. A Critic that reviews judgment, not arithmetic
If there is a reviewer stage, its checks are things code cannot do: does the output match the
decision, did a locked topic leak into an outbound message, is the voice right, was an existing
commitment ignored. Do not re-check what is already legal by construction. The verdict is a
server-side gate: block cannot be approved, revise needs an acknowledged override recorded on the
decision.

## 7. Human gate
Nothing executes without a person. Overrides require a one-line reason and are recorded. Approval
executes only what the output promised, nothing more.

## 8. Trust ladder per category
L0 suggest-only, L1 drafts with per-item approval, L2 auto-handles low-stakes items and logs, L3
bounded autonomy within policy. Promotion requires a measured acceptance rate over a rolling
window. Demotion is automatic on a critical miss. Name the categories locked at L0 permanently,
which no track record can promote.

## 9. Append-only audit
Every stage, every verdict, every external write: timestamped and attributed. No path through the
system leaves no trace.

## 10. Idempotent execution and verdicts
One approval, one record, one external write, even under replay or simultaneous clicks. A
duplicated verdict skews the metric that moves the trust ladder, so this is a data-integrity rule.

## 11. Honest about what is simulated
The model seam and the external adapter can be simulated on day one behind one interface. The
pipeline, policy, trust ladder, and audit run for real. Say which is which.

## 12. Not an agent swarm
Name only what adds capability. Fewer stages with one clear kind each beats many "agents". Two
model calls is a defensible number; ten is a smell.

## Candidate checklist
For each candidate in Phase 2, state in this order:
- Reframe (one sentence)
- Stages, numbered, each tagged with its kind
- Model-call cap and the zero path
- Where the human gate sits and what cannot execute without a person
- Hard-locked categories
- Trade-off versus the other candidates
