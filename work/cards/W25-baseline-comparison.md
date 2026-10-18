# W25 — Draft a measured baseline route comparison

Produce ONE short English Markdown file, maximum 350 words. This is a documentation draft, not a code fix.
Use only the supplied metadata JSON and the supplied baseline requirements. Do not use model memory about the game.

Output sections:
- Observed: table of the three run IDs, gate verdict, measured frames/rendered captures/scene changes/FPS where present.
- Coverage limits: metric checks do not establish character control, first battle, named location transitions,
  name entry, user visual approval, or persistence of a freshly guest-written save.
- Pending: identify B-03 semantic/visual checkpoints and comparison gaps. Keep B-03 open.

Do not invent values absent from the JSON, convert timing into gameplay duration, or claim that B-04 is closed.
The parent will compare each claim to the input records before accepting it.
Return exactly one fenced markdown block for D:/Dev/REA/lab/reports/W25-baseline-draft.md.
