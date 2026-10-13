---
paths:
  - "SPEC.md"
  - "OVERVIEW.md"
---

# The two documents

- `SPEC.md` is how the owner wants the project built: goals, constraints, architecture, features, plans, open questions, deferred ideas.
- `OVERVIEW.md` is the record of what was done: decisions, the dated log, what is installed and configured, measurements, findings, tool notes, cautions, sources.
- A change to what the owner wants goes in `SPEC.md`. Everything else goes in `OVERVIEW.md`. Many events need an entry in both.
- The log in `LOGS.local.md` (not in git) is for high-level changes and decisions only: a decision the owner makes about the project, a change to how the server is built or set up, and a finding that affects a decision. Do not log routine operation (starting, stopping, status checks), document edits, wording changes or tidy-ups. Keep each row to a sentence or two. Never rewrite an earlier row; add a correcting one.
- Label confidence. In `SPEC.md` use DECIDED, DEFAULT, ESTIMATE and UNVERIFIED as defined in its section 0. In `OVERVIEW.md` say whether a claim was tested here, read in source, read in documentation, or inferred.
- Never present an estimate or a single reading as a settled fact.
- Keep the short summary sections of `OVERVIEW.md` (1 to 5) readable by someone who is not technical.
- Use the `record-change` skill for the procedure.
