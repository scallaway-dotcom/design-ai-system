# Brief template

One brief shape for every source. A brief built from a ClickUp task and a brief built from a
meeting transcript have the same fourteen sections in the same order, with the same field names.
Downstream steps (Fork A, Fork B, the decision tree) read only this file, never the raw source.

Rules for filling it:

- Every field gets exactly one of: a value, `[?]` (unknown, to be asked), or `n/a` with a reason.
  Never leave a field blank and never delete a field.
- Every value carries a provenance tag: `(stated: <source ref>)`, `(inferred)`, or `(user, <date>)`
  for answers given during the session. A source ref is a ClickUp link, a comment author and
  timestamp, or a transcript timestamp / speaker.
- Quote stakeholders where they described the problem. Paraphrase everything else.
- Do not propose a design anywhere in sections 1–12. Section 14 is the only place an architecture
  rung appears, and only after the decision tree has been walked.

---

```markdown
# Brief: {short title}

| | |
|---|---|
| Source kind | clickup \| transcript |
| Source refs | {task link(s) with task name as anchor, space / list name} or {transcript file, meeting title, date, attendees} |
| Prepared | {date} by voice-design-ai-system |
| Mode | talk \| scaffold \| undecided |

## 1. Problem statement
{One sentence. What is slow, wrong, or expensive, and for whom.} (provenance)

## 2. Stakeholders
| Person / role | Relationship to the process | Source |
|---|---|---|
| {name or role} | owner \| operator \| requester \| approver \| affected | (provenance) |

## 3. Current process
{Numbered steps. Each step names the actor, the system, and the handoff to the next step.}
1. {actor} does {step} in {system} → hands to {next actor} (provenance)

## 4. Pain points and evidence
- {pain point} — "{quote}" — {who, where} (provenance)

## 5. The judgment inside the process
{What decision is actually being made, and why it has stayed with a human. Trust, not
capability, is the usual answer.} (provenance)

## 6. Inputs and data
| Field | Value | Source |
|---|---|---|
| What arrives (the inbound item) | | |
| Volume (items per day/week/month) | | |
| Where the data lives (systems, docs) | | |
| Historical examples exist? | yes \| no \| [?] | |
| Examples are labeled with the right answer? | none \| some (<100) \| many (100–10k) \| lots (>10k) \| [?] | |
| Does the answer live in documents that could be retrieved? | yes \| no \| partly | |
| Access and permissions | | |
| Sensitive or confidential categories | | |

## 7. Desired outcome and success metric
| Field | Value | Source |
|---|---|---|
| What "better" looks like | | |
| Metric (one number) | | |
| Current baseline for that metric | | |
| Target | | |

## 8. Constraints
| Field | Value | Source |
|---|---|---|
| Latency budget | real-time (<1s) \| interactive (<10s) \| minutes \| batch (hours/overnight) | |
| Cost budget per item or per month | | |
| What must never be automated | | |
| Compliance / policy / legal | | |
| Deadline or forcing event | | |

## 9. Team and maintenance
| Field | Value | Source |
|---|---|---|
| Who owns it after launch | | |
| Engineering capacity | none \| one dev part-time \| small team \| team with ML experience \| platform team with on-call | |
| Who edits the rules / policy (non-engineer?) | | |
| Tolerance for a wrong answer reaching a human | | |
| Tolerance for a wrong answer reaching the outside world | | |

## 10. Prior attempts
- {what was tried, what happened, why it stopped} (provenance)

## 11. Open questions
- [ ] {question} — blocks: {section number it would fill}

## 12. Stated vs inferred ledger
**Stated:** {bullets, each with a source ref}
**Inferred:** {bullets; conclusions no source says outright}
**Not covered by the source at all:** {bullets}

## 13. Decisions log
| When | Decision | Why | Who |
|---|---|---|---|
| {timestamp} | {decision} | {reason in one line} | user \| agent (confirmed by user) |

## 14. Architecture rung
| Axis | Answer | Source |
|---|---|---|
| Problem type | classify \| extract \| generate \| rank \| predict \| plan/schedule \| decide \| converse | |
| Data | {from section 6} | |
| Latency / cost | {from section 8} | |
| Team | {from section 9} | |
| **Starting rung** | R{n} {name} | decision tree |
| Escalation condition | {the measured failure that would justify the next rung} | |
```

---

## Mapping: ClickUp task → brief

| Brief section | Where it comes from |
|---|---|
| Title, source refs | `clickup_get_task` name, url, list and space from `clickup_get_list_location` |
| 1. Problem statement | Task description first paragraph; task name if description is empty |
| 2. Stakeholders | Assignees, watchers, comment authors, people named in description |
| 3. Current process | Description, checklists, subtasks, attached process docs |
| 4. Pain points | Description, comments (quote the comment), chat thread if given |
| 5. Judgment | Usually inferred; mark it so unless a comment states it |
| 6. Inputs and data | Custom fields, attachments, linked docs, comments mentioning volumes or systems |
| 7. Outcome and metric | Custom fields (priority, due date), description "done when", comments |
| 8. Constraints | Due date → deadline; tags; anything marked confidential |
| 9. Team | Assignees, the list's space (which team owns it), comments |
| 10. Prior attempts | Linked or dependent tasks, closed subtasks, comment history |
| 11. Open questions | Whatever is `[?]` after the above |

## Mapping: meeting transcript → brief

| Brief section | Where it comes from |
|---|---|
| Title, source refs | Meeting title, date, attendee list, file name |
| 1. Problem statement | The first time someone names the problem; prefer the owner's phrasing |
| 2. Stakeholders | Speaker labels; people referred to by name |
| 3. Current process | Passages where someone walks through "what happens today" |
| 4. Pain points | Complaints, "the annoying part is", "we always end up"; quote with timestamp |
| 5. Judgment | Passages about "someone has to look at it", "I just know", "depends" |
| 6. Inputs and data | Mentions of spreadsheets, systems, "we have a list of", counts and volumes |
| 7. Outcome and metric | "What I want is", "it would be a win if", numbers people cite as goals |
| 8. Constraints | "we can't", "legal", "has to be instant", "we have no budget", dates |
| 9. Team | Who says they will own it; who says they cannot maintain it |
| 10. Prior attempts | "we tried", "last time", "the old script" |
| 11. Open questions | Questions asked in the meeting and not answered, plus every `[?]` |

Transcripts are noisy. Prefer a quote plus a timestamp over a paraphrase whenever the wording
matters, and record disagreements between speakers in section 4 rather than resolving them.
