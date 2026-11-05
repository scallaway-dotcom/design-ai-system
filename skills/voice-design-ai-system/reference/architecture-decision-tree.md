# Architecture decision tree

Pick the least interesting architecture that could plausibly work, build that, measure it, and
move up one rung only when the measurement says the current rung fails. The tree answers four
questions from the brief and lands on a starting rung. It never lands above the starting rung on
day one, no matter how the problem sounds.

## The rungs

| Rung | Name | What it is | Day-one shape |
|---|---|---|---|
| R0 | Process change | No software. Reorder steps, add a checklist, change who approves, delete the step. | A one-page runbook |
| R1 | Rules and lookups | Deterministic code or a spreadsheet: if/then rules, lookup tables, templates, scheduled reports. | Script or sheet the owner can edit |
| R2 | Classical ML or statistics | Logistic regression, gradient-boosted trees, nearest neighbours, forecasting on labeled history. | Notebook → batch job |
| R3 | One model call behind policy | A single LLM call that writes or classifies, with the outcome set by rules in data, options searched by code, and a human gate. | Prompt + policy file + approval queue |
| R4 | Retrieval before the call | R3 plus retrieval over the documents where the answer actually lives. Still one call. | Index + prompt + approval queue |
| R5 | Staged pipeline with Critic | Four to eight stages, each one kind (deterministic / model / human / external), a Critic that reviews judgment, a trust ladder per category, append-only audit. The Maestro shape. | See `/design-ai-system` |
| R6 | Fine-tuned or custom-trained model | Training on the team's own labeled data because prompting cannot reach the metric. | Training set, eval set, serving |
| R7 | Agentic loop with tools | A model choosing its next action across many dependent tool calls. | Only after R5 has been shown insufficient |

Two model calls is a defensible number. Ten is a smell. Anything that can be a lookup is a lookup.

## The four questions

Answer each from the brief. If the brief says `[?]`, that question goes to the user before the
rung is chosen (Fork A: ask it aloud; Fork B: it is the next interview question).

### Q1. Problem type (brief section 5 and 6)

| Type | Meaning | Floor rung | Notes |
|---|---|---|---|
| classify | Route, triage, tag, yes/no | R1 | Rules first; R2 if labeled history; R3 if labels are scarce and text is messy |
| extract | Pull structured fields from unstructured input | R1 | Regex/parsers for fixed formats; R3 for free text |
| generate | Draft a message, summary, document | R3 | Templates (R1) first if the output barely varies |
| rank / recommend | Order options, suggest the best | R1 | Score by rules; R2 with click/accept history |
| predict | A number or a date in the future | R1 | Moving average / seasonality before any model |
| plan / schedule | Find a legal arrangement under constraints | R1 | Search runs in code; a model only explains the result (R3) |
| decide | A judgment with policy and stakes, currently human | R3 | Policy as data; human gate; escalate to R5 when categories need different trust |
| converse | Multi-turn dialogue with a person | R3 | R4 if answers come from documents; R7 only if actions are required mid-conversation |

### Q2. Available data (brief section 6)

| Data | Effect on rung |
|---|---|
| No examples | Stay at R0–R1. Start collecting: log the human's decision for every item from day one. |
| Examples, unlabeled | R1, or R3 with a human gate so the gate produces labels. |
| Labeled, under 100 | R1 or R3 (few-shot). Too few for R2/R6. |
| Labeled, 100–10k | R2 is now live for classify/predict/rank. R3 for text. |
| Labeled, over 10k | R2 first; R6 only after R2/R3 fail the metric. |
| Answer lives in documents | Adds retrieval: R4 instead of R3. |
| Sensitive categories present | Those categories never reach a model. Zero-path required at any rung ≥ R3. |

### Q3. Latency and cost budget (brief section 8)

| Budget | Effect on rung |
|---|---|
| Real-time (<1s) | R1/R2 only on the hot path; a model call can run beside it, never inside it. |
| Interactive (<10s) | One model call fits (R3/R4). R5 with two calls is borderline; measure it. |
| Minutes | R3–R5 all fit. |
| Batch | Anything fits; prefer the cheaper rung anyway. |
| Cost per item is tight relative to volume | Compute `volume × calls × cost per call`. If it exceeds the budget, drop a rung or add a deterministic filter so most items take the zero path. |

### Q4. Team and maintenance (brief section 9)

| Team | Ceiling rung | Why |
|---|---|---|
| No engineer | R1 | A sheet or a rules file the owner edits. Anything else rots. |
| One developer, part-time | R3/R4 | One prompt, one policy file, one queue. No training pipeline. |
| Small team, no ML experience | R5 | A staged pipeline is operable; a trained model is not. |
| Team with ML experience | R6 | Training and eval can be maintained. |
| Platform team with on-call | R7 | Agentic loops need monitoring and rollback that only an on-call team provides. |

The ceiling wins. A problem that "deserves" R6 with a part-time developer gets R3 and a plan to
collect labels.

## Walking the tree

```
start
├─ Can the process be fixed by changing who does what, or deleting a step?  → yes → R0. Stop.
├─ Q1 floor rung F from the problem type
├─ Q2 data adjustment: raise F to R2 only if labeled ≥100 and type ∈ {classify, predict, rank}
│                      swap R3→R4 if the answer lives in documents
├─ Q3 budget: if real-time, cap at R2; compute cost; drop a rung or add a zero-path filter if over
├─ Q4 team ceiling C
└─ starting rung = min(F adjusted, C). Record it in brief section 14 with the escalation condition.
```

## Escalation rule

Move up exactly one rung when, and only when, all of these are true:

1. A prototype at the current rung has been run on at least 30 real items (not invented ones).
2. It fails the metric named in brief section 7, and the failure is written down with the number.
3. The failure is of a kind the next rung addresses (for example: R1 rules miss cases that need
   reading the text → R3; R3 hallucinates facts that are in the docs → R4; R3 needs different
   trust per category → R5; R3/R4 prompting plateaus below target with >10k labels → R6).
4. The team ceiling (Q4) allows the next rung.

Record every escalation in brief section 13 with the measurement. "It feels like it needs an
agent" is not a measurement.

## Demotion rule

If a higher rung is running and a lower rung would now hit the metric (labels accumulated, rules
clarified, the process changed), drop back. Fewer moving parts is a feature.

## Saying it out loud

For Fork A, the tree is four questions and one sentence:

> "What kind of problem is it, what examples do you have, how fast and how cheap does it need to
> be, and who keeps it running? Then we start at the simplest rung that fits and only climb when a
> real prototype fails a number we wrote down."
