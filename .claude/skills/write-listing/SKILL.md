---
name: write-listing
description: Use when an item is priced and needs listing text and form fields for a specific marketplace. Drafts listings/<marketplace>.md from the item sheet, research, and marketplace profile, then checks it.
---

# Write listing

Produces `listings/<marketplace>.md`. Expects status `priced` (or
`listed`, when adding a second marketplace). Leaves status unchanged.

## Gate

Run `uv run classifieds validate items/<slug>`. Stop on any problem.
Read: `item.md`, the newest `research/*-pricing.md`, and
`marketplaces/<marketplace>.md` in full. Read `photos/manifest.md` to know
what the photos show, so the text and photos agree.

## Never include

- Anything under `## Private notes` in item.md.
- The floor, in any form. `check-listing` will catch a literal match, but
  do not paraphrase it either ("would go as low as...").
- Claims the item sheet does not support.

## Frontmatter

One key per field the profile's `required_fields` lists, plus any field
its `field_options` covers, using values from those options exactly. Take
`price` from `ask` in item.md. Derive bike specifics from the item body.
Anything the item sheet does not say, ask the owner rather than guess.

## Description

Follow the profile's "Tone" and "What buyers care about" sections. Shape:

1. One line: year, brand, model, size, and who it fits.
2. One short paragraph on the bike and why it is good, in plain words.
3. Build list as bullets, upgrades marked.
4. Condition and wear, specific, matched to the photos that show it.
5. Service history.
6. Extras included.
7. Logistics: location, pickup or shipping, payment, and how to reach out.
8. Reason for selling, one sentence, if ordinary.

Stay under `description_max`. Do not use the word "mint" unless it is new.

## Check

Run `uv run classifieds check-listing items/<slug> <marketplace>`. Fix
every problem and rerun until it prints `ok`. Then show the owner the
title and description and ask for edits. Apply edits and check again.
