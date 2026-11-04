# design-ai-system: a Cursor skill that designs a Maestro-shaped AI system for an inefficient process

Date: 2026-11-03
Status: approved for planning

## Purpose

When Steven is pulled into an inefficient process and asked to build an AI system to improve it,
`/design-ai-system` reads the context already in ClickUp, proposes two or three candidate AI
system shapes built on the Maestro principles (deterministic where it decides, model-backed only
where language needs judgment, human-gated execution, trust earned per category, append-only
audit), lets him pick one, and delivers a one-page architecture diagram in the style of
[`maestro-ceo-scheduling/static/architecture.png`](https://github.com/stevencallaway1/maestro-ceo-scheduling/blob/main/static/architecture.png)
plus an executive summary and a context dossier.

## Form and home

- A Cursor Agent Skill. Source of truth is the git repo `~/Projects/design-ai-system`, pushed to
  `github.com/scallaway-dotcom/design-ai-system`.
- `~/.cursor/skills/design-ai-system` is a symlink to the repo, so the skill is available in every
  workspace and edits in the repo are live immediately.
- The machine has no `gh`, no SSH key, and no git credential helper. The initial publish goes
  through the GitHub MCP connector (signed in as `scallaway-dotcom`). The README notes how to set
  up `gh auth login` for ordinary `git push` afterwards.

```
design-ai-system/
  SKILL.md                      the agent: trigger, three phases, two gates, output contract
  README.md                     what it is, how to install (symlink), how to run, how to publish
  reference/
    maestro-principles.md       the "inspired by Maestro" rubric every proposal must answer
    maestro.spec.json           the reference diagram as a spec: worked example and test fixture
    summary-template.md         EXECUTIVE-SUMMARY.md skeleton
  scripts/
    render_diagram.py           spec.json -> architecture.svg, pure Python 3, no dependencies
    svg_to_png.sh               architecture.svg -> architecture.png via headless Chrome, 1580x800
  tests/
    test_render_diagram.py      renderer unit tests
  docs/superpowers/specs/       this document
  docs/superpowers/plans/       implementation plan
```

## Trigger

```
/design-ai-system <clickup task url> [clickup chat channel or thread url]
```

The ClickUp workspace is **staging** (`plugin-clickupstaging-clickupStaging` namespace). The skill
does not fall back to production.

## Phase 1: Intake. Decides nothing.

Pulls, in order:

1. The task: `clickup_get_task` with subtasks and custom fields.
2. The task's comments and every threaded reply: `clickup_get_task_comments`,
   `clickup_get_threaded_comments`.
3. Attachments and linked docs on the task: `clickup_download_task_attachment` for text-like
   attachments (md, txt, csv, pdf), `clickup_list_document_pages` then
   `clickup_get_document_pages` for linked docs. Binary attachments are listed by name only.
4. If a chat URL was passed: `clickup_get_chat_channel_messages` and
   `clickup_get_chat_message_replies` for that channel or thread.
5. One Brain query: `clickup_ask_brain` with a prompt built from the task title and description,
   asking for related tasks, docs, and prior attempts at this process. Polled with
   `clickup_get_brain_response`.

Writes `CONTEXT.md` with these sections:

- **Sources pulled**: each item with its ClickUp link, as inline markdown links.
- **The current process as described**: steps, actors, systems, handoffs, in the stakeholders'
  words where possible.
- **Pain points**: stated by stakeholders, each attributed.
- **People and roles**.
- **Stated vs inferred**: two lists. Nothing in "inferred" is presented as fact later.
- **Gaps**: what the skill needed and could not find.

Rules:

- If the ClickUp tools fail or the task cannot be read, the skill stops, says so, and asks the
  user to paste context. It does not invent context.
- If Brain times out or returns nothing useful, the skill continues and records that in **Gaps**.
- Intake makes no design judgments. No candidate system shapes appear in `CONTEXT.md`.

## Phase 2: Design. Propose, user picks.

### Step 1: candidates

The skill applies the Maestro rubric (below) to `CONTEXT.md` and presents 2 or 3 candidate system
shapes through the AskQuestion tool. Each candidate states:

- A one-line reframe: the judgment hiding inside the process.
- Ordered stages, 4 to 8, each tagged deterministic / model-backed (one call) / human decision
  point / external adapter.
- Model-call cap per run, and the path where the count is zero.
- Where the human gate sits and what cannot execute without a person.
- What is hard-locked (sensitive categories never sent to a model).
- The trade-off against the other candidates.

Lead with the recommended candidate and say why.

**Gate 1**: the user picks one. The skill does not proceed on a guess.

### Step 2: finalize

The skill expands the chosen candidate into the full design and shows it in chat as text:

- Title, subtitle, one-sentence thesis.
- Input box: the inbound item and its channels.
- Stage strip: number, label, kind, title, two- or three-line body for each stage.
- Data sources: which hand-editable files or systems feed which stage.
- Bypass path, if any: the condition that skips model stages and goes straight to a human.
- Execution box: the external adapter and its idempotency note.
- Two bottom panels: audit log, trust ladder and eval loop.
- Feedback arrow: which panel adjusts which stage.
- Caption: two lines stating the model-call cap and what the model never does.
- Trust ladder table: L0 to L3 with promotion gates, the automatic demotion trigger, and the
  categories locked at L0 permanently.
- What is simulated on day one versus real.

**Gate 2**: the user confirms before anything is drawn. Changes loop back to Step 2.

### The Maestro rubric (`reference/maestro-principles.md`)

Every candidate and the final design must answer these. The file is the checklist the skill reads
before proposing.

1. **Reframe.** What judgment is this process really making, and why has it stayed with a human?
   Trust, not capability, is usually the reason software has not taken it.
2. **Stages in order, each tagged.** Deterministic, model-backed (one call), human decision point,
   or external adapter. Intake never decides. Context (the dossier) is a separate stage from
   intake so that flags come from assembled context, not from surface text.
3. **Policy sets the outcome, not the model.** Rules live in data, in plain English, editable by
   the process owner without an engineer. The model writes about the outcome; it does not pick it.
4. **The model cannot invent a resource.** Any search for a legal option (a slot, a vendor, a
   document, an approver) runs before the model call and the model only writes about that list.
5. **Model-call cap stated as a number, with a zero path.** Sensitive categories stop at the
   policy stage and never reach a model.
6. **A Critic that reviews judgment, not arithmetic.** Its checks are things deterministic code
   cannot do: does the output match the decision, did a locked topic leak, is the voice right, was
   an existing commitment ignored. Its verdict is a server-side gate: block cannot be approved,
   revise needs an acknowledged override.
7. **Human gate.** Nothing executes without a person. Overrides require a reason and are recorded.
   Approval executes only what the output promised, nothing more.
8. **Trust ladder per category.** L0 suggest-only through L3 bounded autonomy. Promotion needs a
   measured acceptance rate over a window. Demotion is automatic on a critical miss. Some
   categories are locked at L0 permanently and no track record promotes them.
9. **Append-only audit.** Every stage, verdict, and external write is timestamped and attributed.
   No path leaves no trace.
10. **Idempotent execution and verdicts.** One approval, one record, one external write, even under
    replay or simultaneous clicks.
11. **Honest about what is simulated.** The model seam and the external adapter can be simulated on
    day one; the pipeline, policy, trust, and audit run for real.
12. **Not an agent swarm.** Name only what adds capability. Fewer stages with a clear kind each
    beats many "agents".

## Phase 3: Deliver

Writes to `./ai-system-designs/<task-slug>/` in the current workspace, or
`~/Documents/ai-system-designs/<task-slug>/` when the workspace is the home directory:

- `CONTEXT.md` (from Phase 1)
- `architecture.spec.json`
- `architecture.svg`
- `architecture.png` at 1580x800
- `EXECUTIVE-SUMMARY.md` from `reference/summary-template.md`, with sections: The problem, The
  system, What the model does and what it never does, Approvals and the record, Why this shape,
  What is simulated.

Then embeds `architecture.png` in chat and lists the file paths.

The skill does not write anything back to ClickUp.

## Diagram rendering

The agent writes **JSON, not SVG**. `scripts/render_diagram.py` owns geometry and style and
reproduces the reference layout at 1580x800:

- Title and subtitle on one line, thesis line beneath.
- Legend with four swatches: deterministic (grey border), model-backed one call (blue fill),
  human decision point (amber fill), external system or adapter (dashed border).
- Data-source labels above specific stages with dotted vertical drops.
- Row: dashed input box, arrow, numbered stage cards, arrow, dashed execution box. Card fill
  follows kind. Card count 4 to 8; card width scales to fit.
- Optional red dashed bypass arrow from one stage to another, with a note above it.
- Two bottom panels side by side: audit log on the left, trust ladder and eval loop on the right.
- Optional blue feedback arrow from a panel up into a stage, with a label.
- Two-line caption at the bottom.

### Spec schema (`architecture.spec.json`)

```json
{
  "title": "Maestro",
  "subtitle": "AI scheduling for the Office of the CEO",
  "thesis": "One request, end to end. ...",
  "input": { "label": "REQUEST", "title": "Inbound ask", "lines": ["Email", "Slack", "ClickUp task"] },
  "stages": [
    { "num": 1, "label": "INTAKE", "kind": "deterministic", "title": "Normalize", "body": ["Type, duration,", "urgency, channel.", "Decides nothing."] }
  ],
  "data_sources": [
    { "over": [2], "lines": ["people.json · history.json", "relationship, flags, open threads"] }
  ],
  "bypass": { "from": 3, "to": 6, "note": "Sensitive category: skips both model stages, straight to a human" },
  "execution": { "label": "EXECUTION", "title": "Calendar", "lines": ["Idempotent hold, or", "route with no write.", "Simulated in the demo."], "highlight_last": true },
  "panels": [
    { "title": "Audit log", "body": ["Append-only. ...", "...", "..."] },
    { "title": "Trust ladder & eval loop", "body": ["Approvals and overrides are scored per category. ...", "...", "..."] }
  ],
  "feedback": { "from_panel": 1, "to_stage": 4, "label": "sets how much autonomy this category gets" },
  "caption": ["Model calls are capped at two per request, ...", "about slots that are provably legal. ..."]
}
```

`kind` is one of `deterministic`, `model`, `human`, `external`. `bypass`, `feedback`,
`data_sources`, and `execution.highlight_last` are optional. Card bodies, input/execution lines,
and panel bodies are arrays of at most 3 lines; captions at most 2. `stages` must have 4 to 8
entries or the renderer exits non-zero with a message, and the skill re-plans rather than squeezing
the layout.

Publishing: the GitHub connector (`push_files`) performs the initial publish as a single commit.
Afterwards the local branch is reset to `origin/main` once the trees are verified identical, so
local and remote agree. The README documents `brew install gh && gh auth login` for ordinary
pushes from then on.

`scripts/svg_to_png.sh` runs
`"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless --screenshot=<png> --window-size=1580,800 <svg>`
and fails with a clear message if Chrome is absent, in which case the skill ships the SVG and says
so.

## Testing

1. **Reference reproduction.** `reference/maestro.spec.json` rendered through
   `render_diagram.py` and `svg_to_png.sh` is compared side by side with the downloaded
   `static/architecture.png` from the reference repo. Both are embedded in chat. Acceptance is a
   visual judgment: same structure, legend, stage strip, drops, bypass, panels, feedback, caption.
2. **Renderer unit tests** (`tests/test_render_diagram.py`, stdlib `unittest`): valid SVG for 4,
   6, and 8 stages; valid SVG with no `bypass`, no `feedback`, no `data_sources`; non-zero exit
   and message for 3 and 9 stages; unknown `kind` rejected.
3. **End-to-end dry run.** Create a throwaway task in staging ClickUp describing a realistic
   inefficient process with a few comments, run `/design-ai-system` against it through all three
   phases and both gates, inspect every output file, then delete the task.

## Error handling

| Condition | Behaviour |
|---|---|
| ClickUp tool fails or task unreadable | Stop. Report. Ask user to paste context. |
| Brain times out or is empty | Continue. Record in `CONTEXT.md` Gaps. |
| Chat URL passed but unreadable | Continue without it. Record in Gaps. |
| Chrome missing | Ship SVG. Tell the user. |
| Stage count outside 4 to 8 | Renderer refuses. Skill re-plans. |
| User rejects at Gate 1 or Gate 2 | Loop back to that step. Never proceed on a guess. |

## Out of scope

- Writing anything back to ClickUp.
- Production ClickUp.
- Generating code for the designed system. This skill produces the design and the diagram only.
- Any renderer beyond headless Chrome.
