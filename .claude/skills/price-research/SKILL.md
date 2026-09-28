---
name: price-research
description: Use when an item is at status draft and needs an asking price and floor before listing. Gathers comparable listings, writes a dated research file, and moves the item to priced.
---

# Price research

Produces `research/<today>-pricing.md` with a comps table, a recommended
ask, and a private floor. Ends by moving the item from `draft` to
`priced` (or refreshing an already priced item, which leaves status as is
and just adds a new research file).

## Gate

Run `uv run classifieds validate items/<slug>`. Stop on any problem.
Read `item.md` fully: the size, build tier, upgrades, and condition drive
the comps you look for.

## Gather comps

Aim for at least five comparable listings, more if easy. Prefer sold or
recently removed listings over active ones; active asks run high.

Sources, in order of weight for a bike:

1. Pinkbike BuySell, searched in the browser (load the Chrome tools with
   one ToolSearch call, get tab context, open a new tab). Search the exact
   model and year, then the model across adjacent years. Note listed date
   and whether the listing is marked sold.
2. Web search for the model with "sold" and "for sale" across Pinkbike,
   The Pro's Closet, eBay sold listings, and forum threads.
3. Any marketplace the owner named.

For each comp record: source, URL, title, size, build tier or key parts,
condition as stated, price, currency, listed date, sold or active, and a
note on how it differs from ours.

## Adjust and recommend

Reason about: frame size (unusual sizes sell slower), build tier
relative to ours, upgrades that buyers actually pay for versus ones they
do not, condition, region, and season (bikes sell for more in spring
than in fall). State each adjustment in a sentence.

Recommend an ask that is near the top of the realistic range if the owner
wants a fair price and time, or the middle if they want speed. Ask which.
Set the floor at the price below which the owner would rather keep it;
propose a number and let them change it. The floor never leaves the repo.

## Write the file

`research/<today>-pricing.md`:

```markdown
---
item: <slug>
date: <today>
recommended_ask: <int>
floor: <int>
currency: USD
sources:
  - <source name or URL>
---
# Pricing research: <year> <brand> <model>

## Comps

| source | url | title | size | build | condition | price | listed | status | notes |
|---|---|---|---|---|---|---|---|---|---|

## Reasoning

## Recommendation

Ask <n>. Floor <n>. What would move it: ...
```

## Gate out

After the owner agrees on ask and floor:

- If status is `draft` or `withdrawn`, run
  `uv run classifieds status items/<slug> priced --price <ask> --floor <floor>`
  and show the output.
- If status is already `priced` (a refresh), the status command has no
  transition to apply. Edit `ask`, `floor`, and `updated` in item.md by
  hand, then append `<today>  priced  ask <ask> floor <floor> (refresh)`
  to log.md, and run `uv run classifieds validate items/<slug>`.
- If status is `listed` (re-pricing a live listing), do not post again.
  The listing already exists on the marketplace; the owner edits its
  price there. Steps:
  1. `uv run classifieds status items/<slug> priced --price <ask> --floor <floor>`
  2. For every file in `listings/`, set `price` to the new ask and run
     `uv run classifieds check-listing items/<slug> <marketplace>` until
     it prints `ok`.
  3. Tell the owner the new price and ask them to edit each live listing.
     When they confirm, run
     `uv run classifieds status items/<slug> listed --note "repriced to <ask>"`.
