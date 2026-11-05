---
name: voice-design-ai-system
description: Turns a ClickUp task (from a space or list the user names) or a meeting transcript into one normalized AI-system brief, then either talks the design through conversationally in voice or scaffolds the system and interviews the user to a final design. Picks architecture with a boring-first decision tree (problem type, data, latency/cost, team). Use when the user invokes /voice-design-ai-system, or asks to talk through or scaffold an AI system from a ClickUp task or a meeting transcript.
---

# voice-design-ai-system

Two inputs, one brief, two ways out.

```
ClickUp task (space/list named)  ─┐                      ┌─ Fork A: talk it out (voice)
                                   ├─ normalize → BRIEF.md ┤
Meeting transcript               ─┘        │              └─ Fork B: scaffold + interview → DESIGN.md
                                            └─ architecture decision tree → rung
```

`<skill-dir>` means the directory containing this file. Reference files:

| File | Use |
|---|---|
| `<skill-dir>/reference/brief-template.md` | The normalized brief. Same fields for both sources. Includes the ClickUp→brief and transcript→brief mappings. |
| `<skill-dir>/reference/architecture-decision-tree.md` | Rungs R0–R7, the four questions, escalation and demotion rules. |
| `<skill-dir>/reference/voice-guide.md` | Turn rules for voice, the Fork A talk track, the Fork B interview order. |
| `<skill-dir>/reference/scaffold-template.md` | `DESIGN.md` skeleton for Fork B. |
| `<skill-dir>/../../reference/maestro-principles.md` | The twelve principles a design at rung R3 or above must answer. |

## Invocation

```
/voice-design-ai-system clickup <space or list> [task url | search words] [--mode talk|scaffold]
/voice-design-ai-system transcript <file path | Drive/Docs link | ClickUp Doc url | "paste follows"> [--mode talk|scaffold]
```

The user may also just say it: "talk me through the onboarding task in the Ops list", or "scaffold
an AI system from yesterday's transcript". Map that to the form above.

- **Source is required.** If neither `clickup` nor `transcript` can be inferred, ask which, once.
- **ClickUp space or list is required.** The user always names one. If a ClickUp task URL arrives
  without a space or list, ask for it once and stop until answered. Do not guess a list from the
  task.
- **Mode is optional.** If absent, ask after the brief is confirmed (see voice-guide).

## Hard rules

- ClickUp namespace: production `Clickup` unless the user says staging, then `ClickupStaging`.
  Call `GetDynamicTools` on the chosen namespace once before the first ClickUp call.
- Never write back to ClickUp or edit the transcript source. The outputs live in the workspace.
- Write ClickUp task links as inline markdown links with the task name as anchor text.
- The brief decides nothing. Sections 1–12 of the brief contain no design; section 14 holds the
  rung only after the decision tree has been walked with the user.
- Voice: follow the turn rules in `voice-guide.md`. Three sentences aloud, one question per turn,
  nothing structural read out loud.
- Every user decision is appended to brief section 13 before the next turn.
- Start at the boring end. The starting rung is never above what the decision tree yields, and the
  rung rises only on the escalation rule (a prototype on ≥30 real items failing a written metric).
- Output directory: `./ai-system-briefs/<slug>/` in the current workspace; if the workspace is the
  home directory, `~/Documents/ai-system-briefs/<slug>/`. `<slug>` is the task name or meeting
  title lowercased, non-alphanumerics replaced by `-`, trimmed to 50 chars.

## Step 1: Intake

Copy the matching checklist into a TodoWrite and work it.

### 1A. ClickUp task

```
- [ ] 1. Resolve the named space or list: clickup_get_workspace_hierarchy; match by name
        (case-insensitive, allow a unique prefix). If the name matches nothing, or more than one
        thing, ask the user to pick. Record space id and list id(s).
- [ ] 2. Find the task:
        - URL given: clickup_get_task, then clickup_get_list_location to confirm it is in the named
          space/list. If it is not, say so and ask whether to proceed anyway or pick another.
        - Search words given: clickup_filter_tasks on the list id(s) with the words. One hit:
          take it. Two to five: list them in chat (name, status, assignee) and ask. More than five:
          ask for narrower words.
- [ ] 3. clickup_get_task with description, attachments, custom_fields, subtasks, watchers.
- [ ] 4. clickup_get_task_comments; clickup_get_threaded_comments for any comment with replies.
- [ ] 5. Attachments: for each md/txt/csv/pdf/docx attachment, clickup_download_task_attachment and
        fetch the returned URL immediately (single-use, short-lived) into <out>/attachments/.
        List other attachments by name. Linked docs: clickup_list_document_pages then
        clickup_get_document_pages.
- [ ] 6. Linked and dependent tasks: for each, clickup_get_task (name, status, last comment only).
        These feed brief section 10.
- [ ] 7. Create <out>/ and write SOURCE.md: what was pulled, each item linked.
```

### 1B. Meeting transcript

```
- [ ] 1. Get the text:
        - File path: Read it. Accept .txt, .md, .vtt, .srt, .json (speaker/text arrays), .docx.
        - Google Drive / Docs link: read via the Drive connector.
        - ClickUp Doc url: clickup_list_document_pages then clickup_get_document_pages.
        - "paste follows": take the next user message as the transcript.
- [ ] 2. Normalize the transcript: one line per utterance, `[hh:mm:ss] Speaker: text`. Keep
        timestamps if present; otherwise number the utterances so quotes can still be cited.
        Strip filler words only inside paraphrases, never inside quotes.
- [ ] 3. Identify: meeting title, date, attendees (from header or speaker labels), the owner of
        the problem (who raised it or who was asked to fix it).
- [ ] 4. Create <out>/ and write SOURCE.md: file name or link, title, date, attendees, length,
        and the normalized transcript as an appendix.
```

Transcripts contain disagreement. Keep both sides in the brief; do not pick a winner.

## Step 2: Normalize into the brief

Read `<skill-dir>/reference/brief-template.md` in full. Fill every section using the mapping
table for the source kind. Then:

1. Every field is a value, `[?]`, or `n/a — reason`. Count the `[?]`s.
2. Every value has a provenance tag: `(stated: ref)`, `(inferred)`, or `(user, time)`.
3. Section 12 lists what is stated, what is inferred, and what the source never covered.
4. Section 11 lists every `[?]` as a question, each tagged with the section it would fill.
5. Section 14 is all `[?]` except where sections 6, 8, 9 stated an answer outright.

Write `<out>/BRIEF.md`. Post it in chat. Then confirm it aloud per voice-guide ("Confirming the
brief"). Fix the brief from the user's corrections before forking.

**Gate: the user confirms the brief and names the mode.** Do not fork on a guess.

## Step 3: Fork

### Fork A: talk it out

Follow the Fork A talk track in `voice-guide.md`. Walk the four decision-tree questions aloud,
one per turn, filling brief section 14 as you go, then name the rung with its escalation
condition. Describe one system shape in three sentences. Log every decision in brief section 13
immediately.

Artifacts: `BRIEF.md` updated in place (sections 11, 13, 14). No `DESIGN.md` unless the user asks
to switch to Fork B, in which case continue below without re-asking anything already logged.

### Fork B: scaffold and interview

1. Walk the decision tree on the brief as it stands. Where a question's answer is `[?]`, it
   becomes an interview question (rows 2–5 in the voice-guide table); otherwise fill section 14.
2. Read `<skill-dir>/reference/scaffold-template.md`. Write `<out>/DESIGN.md` with every known
   value filled and every unknown as `[?]`. For rung R3 and above, read
   `<skill-dir>/../../reference/maestro-principles.md` and make the scaffold answer all twelve; for
   R0–R2 state in section 9 that the principles do not apply and why.
3. Post the scaffold in chat and say so aloud (voice-guide, Fork B opening line).
4. Interview in the voice-guide order. One question per turn. After each answer update `DESIGN.md`
   and brief section 13. If an answer changes the rung, say so and re-announce it.
5. Stop when no `[?]` remains or the user says done. Read back the five-sentence summary and ask
   "Shall I lock this in?"
6. On yes: final `DESIGN.md`, with section 13 listing anything deferred. Offer the diagram
   hand-off: build `architecture.spec.json` from DESIGN.md sections 2, 3, 5, 6, 7 and run
   `/design-ai-system` Phase 3 (renderer in `<skill-dir>/../../scripts/`).

## Step 4: Close

Reply with the list of files in `<out>/`, the rung and its escalation condition, and the three to
five decisions most worth the user's attention. Aloud: rung, one-sentence shape, and what happens
next. Everything else in chat.

## Failure rules

| Condition | Do |
|---|---|
| No source kind can be inferred | Ask "ClickUp task or meeting transcript?" once. Stop until answered. |
| ClickUp given, no space or list named | Ask for it once. Stop until answered. Never infer it from the task. |
| Space/list name matches nothing or several | Show the candidates (≤5) and ask. |
| Task URL is outside the named space/list | Say so; ask to proceed or re-pick. |
| ClickUp tool fails | Stop. Say what failed. Ask the user to paste the task text; continue from Step 2 with source kind `clickup` and refs marked `(pasted)`. |
| Attachment URL expired | Re-request once via clickup_download_task_attachment. If it fails again, list by name and record under section 12 "Not covered". |
| Transcript unreadable or wrong format | Say what format was expected. Offer "paste follows". |
| Transcript has no speaker labels | Proceed; cite by utterance number; note it in section 12. |
| Brief has more than ten `[?]` after Step 2 | Say so before confirming; propose starting with Fork A to fill the gaps conversationally. |
| User answers two questions at once | Log both, acknowledge in one sentence, continue the order. |
| User wants a higher rung than the tree yields | Record the request in section 13 as "requested, not justified yet", keep the tree's rung, and write the escalation condition that would justify it. |
| User rejects the brief or the final read-back | Loop back to that step. |

## Worked example (abridged)

> User: "Talk me through the invoice-approval task in the Finance Ops list."

1. Step 1A: resolve "Finance Ops" → list id; `clickup_filter_tasks` on "invoice approval" → one
   hit; pull task, 14 comments, one CSV attachment of last quarter's invoices.
2. Step 2: brief with 4 `[?]` (latency budget, cost budget, who edits rules, labeled examples).
   Aloud: "Finance approves about three hundred invoices a month; two people check vendor,
   amount and PO match by hand; the pain is the back-and-forth on mismatches. Did I get that
   right?"
3. Fork A: judgment = "is this invoice safe to pay without a human looking". Boring fix: the CSV
   shows 80% match on all three fields → R1 rules handle those; the rest queue for a person. Data:
   a quarter of labeled history (approved/rejected) ≈ 900 rows → R2 possible later. Latency: batch.
   Team: one part-time developer → ceiling R3/R4. Rung: **R1**, escalation to R3 if the rules
   queue more than 30% to a human on 30 real invoices.
4. Close: BRIEF.md with 6 decisions logged; offer to scaffold.
