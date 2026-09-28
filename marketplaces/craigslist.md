---
name: Craigslist
url: https://post.craigslist.org/
title_max: 70
description_max: 8000
photo_max: 24
photo_min_px: 600
fee_rate: 0.0
required_fields:
  - title
  - price
  - condition
  - postal_code
  - city
field_options:
  condition: [new, like new, excellent, good, fair, salvage]
---
# Craigslist

Local, anonymous, no fees. Expect scam replies. Buyers search by keyword,
so the title should contain brand, model, year, and size.

Limits above are `unverified` until a real posting run.

## What buyers care about

- Keywords in the title.
- Cash, local, and when they can see it.

## Tone

Plain. State "cash only, local pickup" and "no shipping" if true.

## Posting flow

1. Open the URL above in a new tab and choose the owner's city.
2. Choose "for sale by owner" then the bike category.
3. Fill title (`title`), price (`price`), postal code (`postal_code`),
   city (`city`), condition (`condition`).
4. Paste the description body.
5. Upload photos from `photos/web/` in manifest order.
6. Stop and wait for the owner to review and publish. Craigslist sends an
   email confirmation the owner must click.

## Gotchas

- None recorded yet.
