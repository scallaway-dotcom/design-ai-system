---
name: design-ai-system
description: Designs a Maestro-shaped AI system to improve an inefficient process described in a staging ClickUp task, then renders a one-page architecture PNG, an executive summary, and a context dossier. Use when the user invokes /design-ai-system with a ClickUp task URL.
disable-model-invocation: true
---

# design-ai-system

Turn a process problem that lives in ClickUp into a decided AI system design with a one-page
architecture diagram in the style of Maestro (github.com/stevencallaway1/maestro-ceo-scheduling).

`<skill-dir>` below means the directory containing this file.

## Invocation

```
/design-ai-system <clickup task url> [clickup chat channel or thread url]
```

Task URLs look like `https://app.clickup-stg.com/t/<task_id>` or
`https://app.clickup-stg.com/t/<team_id>/<custom_id>`. Chat URLs contain `/chat/`, `/r/`, or
`/v/cn/<channel>/t/<id>`; if a URL ending in `/t/<id>` is ambiguous, try `clickup_get_task` first
and treat a not-found as a chat thread.

If no task URL is given, ask for one. Do not proceed on pasted text alone unless ClickUp is
unreachable (see Failure rules).

## Hard rules

- ClickUp **staging** only: namespace `plugin-clickupstaging-clickupStaging`. Never production.
- Call `GetDynamicTools` on that namespace once before the first ClickUp call to load schemas.
- Three phases, in order. Two gates. Never skip a gate or proceed on a guess.
- Phase 1 decides nothing. No candidate designs appear in `CONTEXT.md`.
- Never write back to ClickUp.
- Write ClickUp task links as inline markdown links with the task name as anchor text.
- Output directory: `./ai-system-designs/<task-slug>/` in the current workspace. If the workspace
  is the home directory, use `~/Documents/ai-system-designs/<task-slug>/`. `<task-slug>` is the task
  name lowercased, non-alphanumerics replaced by `-`, trimmed to 50 chars.

## Terms

- **Sensitive**, **hard-locked**, and **locked at L0 permanently** name the same set of categories: the ones that stop at the policy stage, never reach a model, and no track record can promote. Use one list for all three.
- **Override** is the human reversing or changing the system's output; it requires a one-line reason. **Acknowledgment** is the human ticking that they read a Critic `revise` finding before approving; it is recorded as `critic_override: true`. They are different acts.
- The Candidate checklist in the rubric is the short form for Phase 2 Step 1. The full design in Phase 2 Step 2 must answer all 12 principles.

## Phase 1: Intake

Copy this checklist into a TodoWrite and work it:

```
- [ ] 1. clickup_get_task (include: description, attachments, custom_fields, subtasks)
- [ ] 1b. From the task name, compute the output directory (see Hard rules) and create it.
        Everything this run writes goes there.
- [ ] 2. clickup_get_task_comments, then clickup_get_threaded_comments for every comment that has replies
- [ ] 3. Attachments: from the task's attachments list, for each md/txt/csv/pdf attachment call
        clickup_download_task_attachment, then fetch the returned URL once, immediately (it is
        single-use and short-lived) with curl into the output directory under attachments/. List
        other attachments by name only. Linked docs: clickup_list_document_pages to get page ids,
        then clickup_get_document_pages.
- [ ] 4. If a chat URL was given: clickup_get_chat_channel_messages, then clickup_get_chat_message_replies for threads
- [ ] 5. clickup_ask_brain with the prompt below; poll clickup_get_brain_response, waiting about
        20 seconds between polls (use AwaitShell), up to 3 polls
- [ ] 6. Write CONTEXT.md into the output directory
```

Brain prompt (fill the braces from the task):

```
Find tasks, docs, and comments related to this process: "{task name}". Context: {first 500 chars
of description}. Return prior attempts to fix it, who owns each step, systems involved, volumes
or timings mentioned, and anything marked sensitive or confidential.
```

### CONTEXT.md format

```markdown
# Context: {task name}

## Sources pulled
- [{task name}]({task url}) — task, {n} comments, {m} attachments
- {one bullet per doc, attachment, chat thread, Brain query, each linked}

## The current process as described
{Numbered steps. Actors, systems, handoffs. Quote stakeholders where they described it.}

## Pain points
- {pain point} — {who said it, linked}

## People and roles
- {name}: {role in this process}

## Stated vs inferred
**Stated:** {bullets, each attributable to a source}
**Inferred:** {bullets; things you concluded that no source says outright}

## Gaps
- {what you needed and could not find; Brain timeouts; unreadable attachments}
```

Everything in "Inferred" stays labelled inferred for the rest of the run.

## Phase 2: Design

Read `<skill-dir>/reference/maestro-principles.md` in full, then `CONTEXT.md`.

### Step 1: candidates

Build 2 or 3 candidate systems. Each must follow the Candidate checklist at the bottom of the
rubric: reframe, numbered stages with kinds, model-call cap and zero path, human gate, hard-locked
categories, trade-off. Stage counts 4 to 8.

Present them with AskQuestion. If AskQuestion is unavailable, present lettered options in chat
and wait for the reply. The recommended candidate goes first with "(Recommended)" in its
label and one sentence of why. Each option label carries the reframe and the stage list in short
form; the full checklist for each goes in the message above the question.

**Gate 1: wait for the pick.** If the user picks "Other", read it and re-propose.

### Step 2: finalize

Expand the chosen candidate into the full design and show it as text in chat, in this order:

1. Title (one word, two at most), subtitle, one-sentence thesis.
2. Input box: the inbound item and its channels (max 3 lines).
3. Stage strip: for each stage `num · LABEL`, kind, title (2–3 words), body (max 3 short lines,
   each under ~22 characters for 6 stages; shorter for 7–8).
4. Data sources: which hand-editable files or systems feed which stage. Two lines each, under
   ~34 characters; adjacent stages are 189px apart and longer lines collide.
5. Bypass path, if any: the condition that skips model stages straight to a human.
6. Execution box: the external adapter, its idempotency note, and whether it is simulated.
7. Two bottom panels: audit log; trust ladder and eval loop (max 3 lines each).
8. Feedback arrow: which panel adjusts which stage, with its label.
9. Caption: two lines stating the model-call cap and what the model never does.
10. Trust ladder table: L0–L3, promotion gates, automatic demotion trigger, permanently locked
    categories.
11. Simulated on day one vs real.
12. Check every number, threshold, and scope statement in the design against **Stated** in CONTEXT.md. Anything not Stated is labelled inferred in the design or removed. A trust tier, rule, or category that applies to items outside the process scope is an error; fix it before Gate 2.

**Gate 2: ask "Draw this?" and wait.** Changes loop back to this step.

## Phase 3: Deliver

1. `cd` into the output directory; every command in this phase runs from there.
2. Write `architecture.spec.json`. Schema and a complete example:
   `<skill-dir>/reference/maestro.spec.json`. Keys: `title, subtitle, thesis, input{label,title,
   lines}, stages[{num,label,kind,title,body}], data_sources[{over,lines}], bypass{from,to,note},
   execution{label,title,lines,highlight_last}, panels[2]{title,body}, feedback{from_panel,
   to_stage,label} (from_panel 0 = left panel, audit log; 1 = right panel, trust ladder),
   returns[{from,to,kind,label}] (optional; a later stage back to an earlier one, `to` 0 = the
   input box; `kind` `fail` draws a red dashed hop under the cards, `loop` a grey run below it),
   caption[2]`. `kind` ∈ `deterministic | model | human | external`.
3. Render:
   ```bash
   python3 <skill-dir>/scripts/render_diagram.py architecture.spec.json architecture.svg
   bash <skill-dir>/scripts/svg_to_png.sh architecture.svg architecture.png
   ```
   If the renderer exits 2, read its errors, fix the spec, re-run. If `svg_to_png.sh` exits 3,
   ship the SVG and tell the user Chrome was not found.
4. Read `architecture.png` with the Read tool and check it: no text overflowing a card, bypass and
   feedback land where intended, caption fits on two lines. Shorten text in the spec and re-render
   if not.
5. Write `EXECUTIVE-SUMMARY.md` from `<skill-dir>/reference/summary-template.md`, filling every
   `{{slot}}`. Cite ClickUp sources inline. Replace each whole `{{...}}` brace, including the guidance inside
   it, with the final prose. No braces remain.
6. Reply with the embedded PNG (`![architecture](<absolute path>)`), the list of output files,
   and the three to five design decisions most worth the user's attention.

## Failure rules

| Condition | Do |
|---|---|
| ClickUp tool fails or task unreadable | Stop. Say what failed. Ask the user to paste the task text and comments. Compute the output directory from the pasted title (Hard rules), then continue from Phase 1 step 6. |
| Brain times out or is empty after 3 polls | Continue. Record it under Gaps. |
| Chat URL unreadable | Continue without it. Record under Gaps. |
| Renderer exit 1 or traceback | Fix JSON syntax or file paths. |
| Renderer exit 2 | Fix the spec per the message. Never pad or truncate silently. |
| Stage count outside 4–8 | Re-plan the stages. Do not squeeze. |
| Chrome missing (exit 3) | Ship SVG. Say so. |
| `svg_to_png.sh` exit 4 | Read the printed Chrome exit status and log tail. If it mentions a sandbox or Chrome aborted, re-run the command outside the sandbox. |
| `svg_to_png.sh` exit 5 | PNG is not 1580x800. Check the SVG viewBox is 0 0 1580 800 and re-run. |
| User rejects at a gate | Loop back to that step. |

## Worked example

`<skill-dir>/reference/maestro.spec.json` is the reference diagram as a spec. Render it to see the
target look before writing a new one:

```bash
python3 <skill-dir>/scripts/render_diagram.py <skill-dir>/reference/maestro.spec.json /tmp/maestro.svg
bash <skill-dir>/scripts/svg_to_png.sh /tmp/maestro.svg /tmp/maestro.png
```
