# Voice guide

How to run both forks when the user is on a voice call. Everything here also works in text; the
difference is turn length and what gets read aloud.

## Turn rules (both forks)

- One idea or one question per turn. Never two questions in one turn.
- Spoken turns are three sentences or fewer. If more is needed, say the short version and put the
  long version in chat.
- Never read aloud: markdown, tables, file paths, URLs, JSON, code. Say "it's in the chat" and put
  it there.
- Numbers are spoken as words with units ("about two hundred items a week"), and written as
  digits in chat.
- Offer at most three options aloud. More than three goes to chat as a lettered list.
- When the user interrupts, stop the current thread and take the new one. Write the parked thread
  into brief section 11 so it is not lost.
- Close every turn with either a question or a clear "your call" so the user knows it is their
  turn.
- Every decision the user makes is appended to brief section 13 at once, before the next turn.

## Confirming the brief (before either fork)

Read back sections 1, 5, 7 and the top two pain points in no more than six sentences. Then:

> "Did I get that right, and is there anything the task or the meeting left out?"

Fix the brief from the answer. Then, unless the mode was given in the invocation:

> "Do you want to talk this through first, or should I scaffold the system and interview you to
> the final design?"

## Fork A: talk it out

The goal is a shared understanding and a logged set of decisions, not a document. The brief is
the only artifact that changes.

Talk track, in order. Skip a step when the brief already answers it with a stated value.

1. **The judgment.** Say the reframe (brief section 5) as a sentence and ask if it is right.
2. **The boring fix.** Ask whether R0 would do: "Before we talk about models, could this be fixed
   by changing who does what, or dropping a step?" Take the answer seriously.
3. **The four questions**, one per turn, in this order: problem type, data (and whether it is
   labeled), latency and cost, team and maintenance. Each answer updates brief section 14.
4. **Name the rung.** "That puts us at rung {n}, {name}: {one sentence of what that looks like}.
   We'd only go higher if {escalation condition}." Ask if that feels right.
5. **One shape, aloud.** Describe the system in three sentences: what comes in, what the human
   sees, what goes out. No stage lists aloud; put the stage table in chat if asked.
6. **The hard parts.** Ask about what must never be automated, and who edits the rules.
7. **Recap and offer.** Recap the decisions in section 13 in four sentences or fewer, then:
   "Want me to scaffold this into a full design and fill the gaps with you, or leave it here?"

If the user says yes to scaffolding, switch to Fork B with the brief as it now stands. Nothing is
re-asked.

## Fork B: scaffold and interview

Write `DESIGN.md` from `scaffold-template.md` first, filling everything the brief and the decision
tree already answer. Say:

> "I've written the scaffold to the chat with the gaps marked. I'll ask about them one at a time;
> say 'skip' to leave one open."

Then interview. Order of questions, each resolving the named `[?]`:

| Order | Resolves | Spoken question |
|---|---|---|
| 1 | §1 reframe (if inferred) | "Is the real decision here {reframe}, or is it something else?" |
| 2 | §14 brief: problem type | "Is this mostly sorting things, pulling fields out, drafting text, ranking options, predicting a number, scheduling, or making a judgment call?" |
| 3 | §14 brief: data | "Do you have past examples, and do they come with the right answer attached?" |
| 4 | §14 brief: latency / cost | "How fast does an answer need to come back, and is there a budget per item or per month?" |
| 5 | §14 brief: team | "Who keeps this running after launch, and how much engineering time do they have?" |
| — | rung | Announce the rung and the escalation condition. Not a question. |
| 6 | §2 inbound item and channels | "What exactly arrives, and from where?" |
| 7 | §2 output and destination | "What should come out the other end, and where does it land?" |
| 8 | §4 zero path | "Which items should never touch a model at all?" |
| 9 | §5 hard-locked categories | "What must never be automated, no matter how good the track record gets?" |
| 10 | §5 who edits policy | "Who should be able to change the rules without calling an engineer?" |
| 11 | §6 approver and what approval executes | "Who approves, and when they click approve, what exactly happens?" |
| 12 | §7 trust categories | "Are there kinds of items you'd trust it with sooner than others?" |
| 13 | §8 labels collected from day one | "Can we record the human's decision on every item from day one so we build up examples?" |
| 14 | §9 simulated vs real | "On day one, which parts can be pretend and which have to be real?" |
| 15 | §10 prototype plan | "Who can judge thirty real items, and by when?" |
| 16 | §11 bus factor | "If the owner left tomorrow, what breaks?" |

Rules for the interview:

- Ask only questions whose slot is still `[?]`. Rows 2–5 are skipped when the brief has stated
  values.
- After each answer, update `DESIGN.md` and brief section 13, then ask the next question. Do not
  batch.
- If an answer changes the rung (for example the team turns out to have no engineer), say so and
  re-announce the rung before continuing.
- "Skip" moves the item to §13 Open items with the user as owner.
- Stop when no `[?]` remains or the user says they are done. Then read back §1, the rung, the
  stage count, the model-call cap, and the human gate in five sentences or fewer, and ask:
  "Shall I lock this in?"
- On yes, write the final `DESIGN.md`, and offer the diagram hand-off to `/design-ai-system`.
