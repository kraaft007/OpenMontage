# Visual Reference Board — research-stage addendum

Local extension. Read this alongside `skills/pipelines/<pipeline>/research-director.md`;
it adds a step rather than replacing anything. Nothing upstream imports it.

## When to use

The research director's search batches assume visual references are things you
*found* — URLs with descriptions. That covers the web, and misses two cases
that come up constantly:

1. The user generated reference stills themselves (their own Gemini, Runway or
   Midjourney subscription) and dropped them in the project.
2. A tool generated candidates and a human now has to choose between them.

In both cases the references are files on disk, and the research brief's
`visual_references` array cannot hold them — its items accept only
`description`, `url` and `what_works`, with `additionalProperties: false`.

## Step A — record them without changing the schema

`research_brief.metadata` is declared `{"type": "object"}` with no constraints,
so local references validate today under `metadata.local_visual_references`:

```json
{
  "label": "F1 forward canopy",
  "local_path": "assets/images/F1-canopy-a.jpg",
  "what_works": "control within reach of the seated figure",
  "defects": ["US flag patch on shoulder"]
}
```

Paths are relative to the project directory so the brief survives the project
being moved. Do not edit `schemas/artifacts/research_brief.schema.json` for
this — it is an upstream file and the change is unnecessary.

## Step B — build a board before asking for a decision

**A human cannot choose between images they cannot tell apart.** Filenames are
invisible when images are viewed side by side, and labels that exist only in
chat force the user to cross-reference by hand. Render the labels into the
picture:

```python
registry.discover("om_ext")
registry._tools["contact_sheet"].execute({
    "title": "<project> — <what is being chosen>, <date>",
    "rows": [
        {"label": "F1  FORWARD CANOPY  — intimate, control in reach",
         "images": ["<project>/assets/images/F1-canopy-a.jpg", ...]},
    ],
    "output_path": "<project>/assets/images/CONTACT-SHEET-<subject>.jpg",
})
```

Group one row per option, not one row per image — the row label is what the
user will say back to you. Name files so the basename carries the label too
(`F2-command-deck-b.jpg`, not `Unknown-5`); the caption under each cell is the
basename, and the user sees the same string in their file browser.

Name known defects in the filename where one exists
(`F2-command-deck-c-second-figure.jpg`). It stops the user having to
re-discover the flaw, and stops a later stage picking that frame by accident.

## Step C — present the trade-off, not just the pictures

For each option say what it *gives* and what it *costs* against the specific
brief. A formation that looks best is not the same as one that can stage the
required action — check that whatever the script asks the subject to do is
physically possible in the room shown. A chair with no console in reach cannot
support "presses the control".

## Cost

Zero. `contact_sheet` is local and deterministic.
