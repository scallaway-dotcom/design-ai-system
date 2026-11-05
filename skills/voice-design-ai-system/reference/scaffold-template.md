# Scaffold template (Fork B)

The scaffold is the final design with holes in it. Write it to `DESIGN.md` immediately after the
brief is confirmed, with every unknown as a `[?]` placeholder, then interview the user until no
`[?]` remains. The interview order is in `voice-guide.md`.

Rules:

- Copy the whole template. Never drop a section; write `n/a — {reason}` instead.
- Sections that the decision tree fixes (rung, stage count, model-call cap) are filled from brief
  section 14, not asked again.
- Keep every answer attributable: `(brief §n)`, `(user, {timestamp})`, or `(decision tree)`.
- A design above R2 must also satisfy the twelve Maestro principles in
  `../../reference/maestro-principles.md`. Below R2 that file does not apply; say so in section 9.

---

```markdown
# Design: {title}

**{one-line what it is}**
Source brief: BRIEF.md · Rung: R{n} {name} · Mode: scaffold

## 1. Reframe
{One sentence: the judgment this process is making and why it has stayed with a human.} (brief §5)

## 2. What goes in, what comes out
| | |
|---|---|
| Inbound item | [?] |
| Channels it arrives on | [?] |
| Output per item | [?] |
| Where the output lands (system, queue, person) | [?] |

## 3. Stages
{R0: one line. R1–R2: the steps of the script or job. R3+: four to eight stages.}

| # | Stage | Kind | What it does | Inputs | Outputs |
|---|---|---|---|---|---|
| 1 | Intake | deterministic | [?] | | |
| 2 | Context | deterministic | [?] | | |
| 3 | Policy | deterministic | [?] | | |
| 4 | [?] | model | [?] | | |
| 5 | Review | human | [?] | | |
| 6 | Execute | external | [?] | | |

Kinds: `deterministic` · `model` (one call) · `human` · `external`. Intake never decides.

## 4. Model calls
| | |
|---|---|
| Maximum model calls per item | {number} (decision tree, brief §14) |
| The zero path (items that never reach a model) | [?] |
| What the model writes | [?] |
| What the model never chooses | the outcome; any resource (slot, vendor, approver, document, budget line) |

## 5. Policy as data
| | |
|---|---|
| Where the rules live | [?] (file, sheet, table) |
| Who edits them without an engineer | [?] (brief §9) |
| Hard-locked categories (never automated, no track record promotes them) | [?] (brief §8) |

## 6. Human gate
| | |
|---|---|
| Who approves | [?] |
| What approval executes, exactly | [?] |
| What approval deliberately does not do | [?] |
| Override: one-line reason required and recorded | yes |

## 7. Trust ladder (R3 and above)
| Category | Day-one level | Promotion gate | Demotion trigger |
|---|---|---|---|
| [?] | L0 | acceptance ≥ [?]% over [?] items | one critical miss |
| {locked} | L0 permanently | none | — |

L0 suggest-only · L1 draft with per-item approval · L2 auto-handle low stakes and log · L3 bounded autonomy within policy.

## 8. Data, latency, cost
| | |
|---|---|
| Data used, and where it lives | (brief §6) |
| Labels: what is collected from day one | [?] |
| Latency budget and the path that meets it | (brief §8) |
| Cost estimate: volume × calls × cost per call | [?] |

## 9. Audit, idempotency, simulation
| | |
|---|---|
| Audit record per stage (timestamped, attributed, append-only) | [?] |
| Idempotency: one approval → one record → one external write | [?] |
| Simulated on day one | [?] |
| Real on day one | [?] |
| Maestro principles applicability | applies (R3+) \| does not apply (R0–R2) |

## 10. Success metric and prototype plan
| | |
|---|---|
| Metric (brief §7) | |
| Baseline → target | |
| Prototype: items to run (≥30 real ones), who judges, by when | [?] |
| Escalation condition to R{n+1} | (brief §14) |
| Demotion condition | [?] |

## 11. Ownership
| | |
|---|---|
| Owner after launch | (brief §9) |
| Engineering capacity assumed | (brief §9) |
| What breaks if the owner leaves | [?] |

## 12. Decisions made in this session
{Copy of brief §13.}

## 13. Open items
- [ ] {anything still `[?]` the user chose to defer, with who owns answering it}

---
Hand-off: to render the one-page diagram, run `/design-ai-system` Phase 3 with an
`architecture.spec.json` built from sections 2, 3, 5, 6 and 7 of this file.
```
