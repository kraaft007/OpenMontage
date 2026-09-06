# om_ext — local extensions

Everything here is ours. Upstream `calesthio/OpenMontage` has no `om_ext/`
directory, so `git merge upstream/main` can never conflict with anything in it.

## Why it exists

Adding capability by editing `tools/`, `skills/` or `schemas/` creates a
permanent merge burden: every upstream change to those files has to be
reconciled by hand. This package holds additions instead, so the only files
that ever conflict are ones we deliberately *fixed* upstream — and those belong
in a pull request, not here.

## How the registry finds it

`ToolRegistry.discover()` already takes a `package_name` argument that nothing
upstream passes a non-default value to. That is the seam:

```python
registry.discover()            # 121 upstream tools
registry.discover("om_ext")    # + ours
```

No upstream file is modified. The trade-off is real and worth stating: any
caller that only runs the default `discover()` — the Backlot board, an upstream
test — will not see these tools. That is acceptable for agent-driven
production, where the agent runs preflight itself, and it is the price of zero
merge conflicts.

## Contents

| Path | What |
|---|---|
| `tools/contact_sheet.py` | Labelled contact sheets from image sets. Local, $0. |
| `skills/visual-reference-board.md` | Research-stage addendum: record local reference images and build a board before asking for a decision. |
| `tests/` | Collected by the normal `pytest` run; rootdir has no `testpaths` restriction. |

## Conventions

- Never import `om_ext` from anything under `tools/`, `lib/` or `skills/`.
  The dependency arrow points one way; if it ever reverses, the isolation is gone.
- Prefer riding in an existing free-form field over editing a schema.
  `research_brief.metadata` is unconstrained and takes local reference data today.
- If something here turns out to be a fix rather than an addition, move it
  upstream as a PR instead of keeping it.
