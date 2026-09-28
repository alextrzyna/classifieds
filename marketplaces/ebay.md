---
name: eBay
url: https://www.ebay.com/sl/sell
title_max: 80
description_max: 4000
photo_max: 24
photo_min_px: 500
fee_rate: 0.1325
required_fields:
  - title
  - price
  - condition
  - category
  - shipping
field_options:
  condition: [New, Used]
  shipping: [Local pickup only, Calculated, Flat rate, Freight]
---
# eBay

National reach, buyer protection, and fees. `fee_rate` above is the
approximate final value fee for sporting goods and is `unverified`; check
the current rate before pricing. Shipping a full bike needs a bike box
and usually a bike shop's help, so price the ask to cover fees and
packing.

## What buyers care about

- Exact model, year, and size in the title.
- Item specifics filled in, since eBay search filters on them.
- Shipping cost and handling time.

## Tone

Factual. Lead with specifics. Describe flaws with photos.

## Posting flow

1. Open the URL above in a new tab. If a login page appears, stop and ask
   the owner to log in.
2. Search the item name and pick or skip the catalog match.
3. Fill title (`title`), category (`category`), condition (`condition`).
4. Upload photos from `photos/web/` in manifest order.
5. Fill item specifics from the listing frontmatter where field names
   match.
6. Paste the description body.
7. Fill price (`price`) as a fixed price, and shipping (`shipping`).
8. Stop and wait for the owner to review and list it.

## Gotchas

- None recorded yet.
