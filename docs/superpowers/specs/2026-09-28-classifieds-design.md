# Classifieds: selling items on online marketplaces

**Date:** 2026-09-28
**Status:** approved design, pending implementation plan

## 1. Purpose

A repo of Claude Code skills, a small Python toolkit, and per-item folders that
take an item from "I want to sell this" to a posted marketplace listing, with
the research and artifacts kept alongside the item.

First item: a 2021 Ibis Ripmo V2 mountain bike, listed on Pinkbike BuySell.
The owner has a Pinkbike account and photos on their phone (not yet exported).

### Success criteria

- One command-free path: run the `sell-item` skill on an item folder and end
  with a filled Pinkbike sell form in the owner's logged-in Chrome, waiting
  only for them to review and click Post.
- Every item keeps an auditable pricing research file (comps table,
  recommended ask, private floor) and a log of status and price changes.
- The layout and skills are marketplace-agnostic. Pinkbike is the first
  adapter; Facebook Marketplace, Craigslist, and eBay follow the same shape.

### Constraints and decisions already made

- Automation stops before submit. Claude fills the form; the owner posts.
- Photos are copied into the repo under the item folder.
- Approach B: markdown skills plus a Python toolkit for the mechanical parts
  (validation, photo prep, listing checks, status transitions). The toolkit
  never writes prose.
- Pricing research produces a comps table plus recommended ask and floor.
  Sale-outcome learning across items is out of scope for now.

## 2. Repository layout

```
classifieds/
  README.md                  what this is, how to sell an item
  CLAUDE.md                  conventions for Claude sessions in this repo
  .gitignore
  pyproject.toml             uv-managed; package lives in tools/
  .claude/skills/
    new-item/SKILL.md
    prep-photos/SKILL.md
    price-research/SKILL.md
    write-listing/SKILL.md
    post-listing/SKILL.md
    sell-item/SKILL.md
  marketplaces/
    pinkbike.md
    facebook.md
    craigslist.md
    ebay.md
  items/
    <slug>/                  e.g. 2021-ibis-ripmo-v2
      item.md
      photos/raw/            files as they came off the phone
      photos/web/            generated, ordered, resized, metadata stripped
      photos/manifest.md
      research/YYYY-MM-DD-pricing.md
      listings/<marketplace>.md
      log.md
  tools/
    classifieds/             Python package
      __init__.py
      cli.py                 argparse entry point
      items.py               load and validate item.md
      photos.py              raw -> web pipeline
      listings.py            check a listing against a marketplace profile
      status.py              status transitions and log entries
      profiles.py            load marketplace profile frontmatter
    tests/
      fixtures/              tiny sample images, sample item and profile files
      test_*.py
  docs/superpowers/specs/    this document
  docs/superpowers/plans/    implementation plans
```

## 3. Data model

All data files are markdown with YAML frontmatter. The toolkit reads the
frontmatter; skills read both frontmatter and body.

### 3.1 item.md

Frontmatter (required unless noted):

| key | type | notes |
|---|---|---|
| slug | string | matches folder name |
| status | enum | draft, priced, listed, sold, withdrawn |
| category | string | e.g. bike, bike-part, electronics |
| brand | string | |
| model | string | |
| year | int | |
| size | string | optional; e.g. frame size, shoe size |
| condition | string | free text short label, e.g. "very good, used" |
| location | string | city and region shown publicly |
| ask | int | optional until priced; whole currency units |
| floor | int | optional until priced; private, never published |
| currency | string | default USD |
| marketplaces | list | optional; where it is or will be listed |
| created | date | |
| updated | date | maintained by the status command |

Body sections (headings, free prose, skills fill them via interview):
Overview, Build and specs, Upgrades and changes from stock, Condition and
wear, Service history, Included extras, Reason for selling, Private notes
(never copied into a listing).

### 3.2 photos/manifest.md

Frontmatter: `max_long_edge` (int, default 2048), `quality` (int, default 88).
Body: an ordered markdown table with columns raw file, web name, caption.
The first row is the hero shot. Web names are `NN-descriptor.jpg`.

### 3.3 research/YYYY-MM-DD-pricing.md

Frontmatter: `item`, `date`, `recommended_ask`, `floor`, `currency`,
`sources` (list). Body: comps table (source, URL, title, size, condition,
price, listed date, sold or active, notes), then reasoning, then the
recommendation and what would move it.

### 3.4 listings/<marketplace>.md

Frontmatter holds every structured field the marketplace form needs, keyed by
the field names in that marketplace profile (e.g. `title`, `price`,
`frame_size`, `wheel_size`, `condition`, `shipping`). Body is the listing
description exactly as it will be pasted. Photo order comes from the manifest.

### 3.5 marketplaces/<name>.md

Frontmatter (read by the toolkit):

| key | notes |
|---|---|
| name | display name |
| url | sell or post page |
| title_max | characters |
| description_max | characters |
| photo_max | count |
| photo_min_px | shortest side |
| fee_rate | fraction; 0 if none |
| required_fields | list of frontmatter keys a listing must have |
| field_options | map of field -> allowed values, where the form is a dropdown |

Body (read by skills): posting flow step by step, what buyers on that site
care about, tone notes, gotchas discovered during real posts. The body is
updated after each real posting run so it stays ground truth.

The Pinkbike profile starts from what is verifiable on their public sell
page. Anything unverified is marked as such and confirmed during the first
`post-listing` run.

### 3.6 log.md

Append-only dated entries: `YYYY-MM-DD  <event>  <detail>`. Events: created,
priced, listed, price-change, inquiry, sold, withdrawn, note.

## 4. Toolkit

Package `classifieds` in `tools/`, Python 3.11+, managed with `uv`.
Dependencies: PyYAML, Pillow, pillow-heif. Tests with pytest. Entry point
`classifieds` via `[project.scripts]`.

Commands:

- `classifieds validate <item-dir>`: required frontmatter present and typed,
  status is a legal value, files implied by status exist (priced requires a
  research file and ask/floor; listed requires a listing file for each entry
  in `marketplaces`). Exit 1 with a list of problems.
- `classifieds photos <item-dir>`: for each manifest row, read the raw file
  (HEIC, JPEG, PNG), resize so the long edge is at most `max_long_edge`,
  re-encode as JPEG at `quality` with no EXIF or GPS, write to
  `photos/web/<web name>`. Skips rows whose output is newer than the input.
  Errors if a raw file is missing.
- `classifieds check-listing <item-dir> <marketplace>`: loads the profile and
  the listing, checks title and description lengths, required fields present,
  dropdown fields within `field_options`, price is at or above floor, and the
  web photo count is within `photo_max` and each web photo meets
  `photo_min_px`. Exit 1 with a list of problems.
- `classifieds status <item-dir> <new-status> [--price N] [--note TEXT]`:
  enforces transitions (draft->priced, priced->listed, listed->sold,
  listed->withdrawn, listed->priced for re-pricing, withdrawn->priced),
  updates `status` and `updated`, sets `ask` when `--price` is given, and
  appends a log entry.

Design rules: pure functions in the modules, I/O only at the edges in
`cli.py`, no network access anywhere in the toolkit.

## 5. Skills

All skills begin by running `classifieds validate` on the item and stop on
failure. Each skill states which status it expects and which it leaves.

- `new-item`: interviews the owner section by section (brand, model, year,
  size, build, upgrades, condition, service, extras, location, reason),
  creates `items/<slug>/` with `item.md` at status draft, an empty
  `photos/raw/`, a manifest with no rows, and `log.md` with a created entry.
- `prep-photos`: expects raw photos in `photos/raw/`. Views them, proposes a
  hero shot and an order that covers what buyers on the target marketplace
  want (drive side, non-drive side, detail shots of wear, components,
  serial or proof of ownership if the profile asks), writes the manifest,
  runs `classifieds photos`, and shows the result for approval.
- `price-research`: gathers comparable listings using web search and, for
  Pinkbike BuySell, the browser. Records at least five comps where they
  exist, notes sold versus active, adjusts for size, build tier, condition,
  region, and time of year, writes the dated research file, and runs
  `classifieds status priced --price N` after the owner agrees on the ask
  and floor.
- `write-listing`: drafts `listings/<marketplace>.md` from item.md, the
  latest research file, and the marketplace profile body. Never copies the
  Private notes section or the floor. Runs `classifieds check-listing` and
  fixes problems before presenting the draft.
- `post-listing`: loads the Chrome tools, opens the marketplace sell URL in
  a new tab in the owner's logged-in browser, fills each field named in the
  listing frontmatter following the profile's posting flow, uploads
  `photos/web/*` in manifest order, pastes the description, then stops and
  tells the owner to review and click Post. If a form field or option does
  not match the profile, it stops, reports the difference, and updates the
  profile body before continuing. After the owner confirms it is posted, it
  runs `classifieds status listed`, records the listing URL in log.md, and
  adds the marketplace to `marketplaces` in item.md.
- `sell-item`: orchestrator. Given an item folder and a marketplace, checks
  status and runs whichever of the above are still needed, in order.

## 6. Error handling

- Validation is the gate between steps. A skill never proceeds past a
  failing validate or check-listing.
- The photo command fails loudly on missing raw files rather than skipping.
- `post-listing` treats any mismatch between the live form and the profile
  as a stop-and-report, not a guess. It never clicks Post.
- The floor is only ever in item.md, the research file, and log.md.
  check-listing fails if the floor appears in listing text.

## 7. Testing

- pytest for the toolkit: validation (good and bad items), status
  transitions (legal and illegal), listing checks against a fixture profile
  (lengths, required fields, options, floor leak, photo count), and the
  photo pipeline on tiny fixture images (resize, format, metadata stripped,
  idempotent skip).
- Skills are verified by running the full pipeline on the Ripmo, which is
  also how the Pinkbike profile gets its first confirmed field list.

## 8. Out of scope

- Submitting listings automatically.
- Message or inquiry handling on the marketplace.
- Cross-item sale analytics.
- Facebook, Craigslist, and eBay posting flows beyond a starter profile.
