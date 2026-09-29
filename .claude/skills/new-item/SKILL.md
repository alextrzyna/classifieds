---
name: new-item
description: Use when the owner wants to sell something new and no items/<slug>/ folder exists for it yet. Interviews the owner and creates the item sheet at status draft.
---

# New item

Creates `items/<slug>/` with `item.md`, `log.md`, an empty `photos/raw/`,
and a manifest with no rows. Ends at status `draft`.

## Gate

If `items/` does not exist, run `uv run classifieds init-items` first. It
creates the private items directory as its own git repo, ignored by the
toolkit repo. Never create `items/` by hand with mkdir.

## Slug

`<year>-<brand>-<model>` lowercased, spaces and punctuation replaced with
dashes, e.g. `2021-ibis-ripmo-v2`. Confirm the slug with the owner before
creating anything. If the folder already exists, stop and say so.

## Interview

Ask in this order, one topic per message, and accept "skip" for anything
the owner does not know. Keep answers verbatim in the item body; do not
polish them into listing prose here.

1. What is it: category, brand, model, year, size.
2. Build and specs: for a bike, fork, shock, drivetrain, brakes, wheels,
   tires, dropper, cockpit, and anything else notable.
3. Upgrades and changes from stock, and what is still stock.
4. Condition and wear: honest and specific. Chips, scratches, bearing
   play, suspension feel, drivetrain wear, tire life. Any crashes.
5. Service history with approximate dates.
6. Included extras: spare parts, tools, original boxes, receipts.
7. Reason for selling, in one sentence.
8. Location as it should appear publicly, e.g. "Seattle, WA".
9. Private notes: anything the owner wants remembered but never published,
   such as the lowest price they would truly take, or who else has asked.

## Write the files

`item.md` frontmatter, all keys required unless noted:

```yaml
---
slug: <slug>
status: draft
category: <bike | bike-part | electronics | ...>
brand: <Brand>
model: <Model>
year: <int>
size: <string, omit if not applicable>
condition: <short label, e.g. "very good, used">
location: <City, ST>
currency: USD
created: <today as YYYY-MM-DD>
---
```

Body headings, in this order, each filled from the interview:

```
# <year> <brand> <model>

## Overview
## Build and specs
## Upgrades and changes from stock
## Condition and wear
## Service history
## Included extras
## Reason for selling
## Private notes
```

`log.md` gets one line: `<today>  created  <one-line summary>`.

`photos/manifest.md`:

```markdown
---
max_long_edge: 2048
quality: 88
---
# Photos

Drop raw photos in photos/raw/, then run the prep-photos skill.

| raw | web | caption |
|---|---|---|
```

## Gate

Run `uv run classifieds validate items/<slug>` and show the output. Fix
any reported problem before finishing. Tell the owner the next step is to
put photos in `items/<slug>/photos/raw/` and run the prep-photos skill.
