---
name: sell-item
description: Use when the owner says they want to sell something, or wants to continue selling an item already in items/. Orchestrates new-item, prep-photos, price-research, write-listing, and post-listing in order, skipping steps already done.
---

# Sell item

Runs the pipeline for one item on one marketplace. Ask for the item (or
the slug) and the marketplace if not given. Default marketplace for a
bike is pinkbike.

## Decide where to start

If `items/<slug>/` does not exist: run the new-item skill first.

Otherwise run `uv run classifieds validate items/<slug>` and read the
status:

| status | photos/web empty | next skill |
|---|---|---|
| draft | yes | prep-photos, then price-research |
| draft | no | price-research |
| priced | any | write-listing if listings/<marketplace>.md is missing, else post-listing |
| listed | any | ask: re-price (price-research, which updates the live listing rather than posting again), add another marketplace (write-listing then post-listing for it), mark sold, or withdraw |
| sold or withdrawn | any | say so and stop unless the owner wants to relist |

Photos are needed before write-listing, so if `photos/web/` is empty at
`priced`, run prep-photos first.

## Run each skill

Invoke each skill with the Skill tool, one at a time, and let it finish
before starting the next. After each, re-run validate. Stop and report if
any gate fails.

## Finish

State the item's status, the listing URL if posted, and what the owner
should watch for next: inquiries on the marketplace, and running the
status command with `sold` or `withdrawn` when it closes.
