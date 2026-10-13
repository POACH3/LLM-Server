---
name: record-change
description: Record a high-level change, decision or finding in the project's documents (SPEC.md, OVERVIEW.md and the log in LOGS.local.md), following the owner's rule for which file holds what. Use after the owner makes a decision about the project, after a change to how the server is built or set up, after a finding that affects a decision, and whenever the owner says to document something. Not for routine operation or document edits.
---

# Recording a change

The owner split the documentation on 2026-10-12. Keep to the split.

| Goes in `SPEC.md` | Goes in `OVERVIEW.md` | Goes in `LOGS.local.md` |
| --- | --- | --- |
| What the owner wants built: goals, constraints, architecture, features, plans, open questions, deferred ideas | What exists: decisions, what is installed and how it is set up, measurements, findings, notes from tool documentation and source code, cautions | The dated log: one short row per high-level change or decision. Not in git |

A single event often touches more than one. Example: the owner chooses to build a logging relay. The feature and its place in the plan go in `SPEC.md`; the decision, the options considered and what was found in the tools go in `OVERVIEW.md`; one row saying it was decided goes in the log.

## What gets a log row

Only high-level changes and decisions:

- a decision the owner makes about the project
- a change to how the server is built or set up
- a finding that affects a decision

Not logged: routine operation (starting, stopping, status checks), document edits, wording changes, tidy-ups, and checks that found nothing.

## Steps

1. **Add a log row**, if the event qualifies, at the end of the table in `LOGS.local.md`. Format: `| YYYY-MM-DD | What was decided or changed, in a sentence or two. |`
2. **Update the as-built sections of `OVERVIEW.md`** if the setup changed: section 3 (day to day), 5 (what is saved), 6 (decisions table), 8 (measurements), 9 (known issues), 10 (components, files, settings), 11 (tool notes), 12 (cautions). The detail belongs here, not in the log row.
3. **Update `SPEC.md`** only if what the owner wants changed: a feature in section 6, the plan in section 7, a question in section 9, an idea in section 10, or the "Where we are" line in the handoff.
4. **Update the "As of" date** at the top of `SPEC.md` or `OVERVIEW.md` if you changed it.

## Writing

- Keep a log row to a sentence or two. Put the detail in `OVERVIEW.md`.
- In `OVERVIEW.md`, say how each claim is known: tested here, read in the source, read in documentation, or inferred. Mark what was not verified.
- Give real numbers with their conditions, and say when a figure is a single reading.
- Record mistakes plainly, with the cause and the fix.
- Never paste a secret, a password, or the text of anyone's prompt or reply.
- Do not rewrite earlier log rows. If one turns out wrong, add a new row that corrects it.

## After editing

Tell the owner in a sentence or two which file changed and why. Commit only when the owner asks.
