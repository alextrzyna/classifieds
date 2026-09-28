---
name: Pinkbike BuySell
url: https://www.pinkbike.com/buysell/selectcategory/
title_max: 100
description_max: 5000
photo_max: 12
photo_min_px: 800
fee_rate: 0.0
required_fields:
  - title
  - price
  - currency
  - category
  - condition
  - frame_size
  - wheel_size
  - frame_material
  - front_travel
  - rear_travel
  - country
  - region
  - city
  - shipping
field_options:
  condition: [New, Excellent, Good, Fair, Poor]
  wheel_size: ["29", "27.5", "27.5+", "26", "Mullet", "700c", "650b"]
  frame_material: [Carbon, Aluminum, Steel, Titanium]
  shipping: [Local pickup only, Will ship, Will ship internationally]
---
# Pinkbike BuySell

Pinkbike is the main used-bike market for mountain bikers in North America.
Buyers are enthusiasts who know the parts and will ask about them. Listings
that get replies show the drive side clearly, state the frame size early,
and list the build honestly, including wear.

Limits and dropdown options above are `unverified` until the first real
posting run. On that run, compare every field against the live form and
correct this file before filling anything.

## What buyers care about

- Frame size and rider height range, stated in the title or first line.
- Full build: fork, shock, drivetrain, brakes, wheels, dropper, tires.
- Upgrades from stock, and what is still stock.
- Wear: paint chips, bearing play, suspension service dates, drivetrain life.
- Whether it has been crashed, and any warranty or frame history.
- Location and whether you will ship. Shipping a bike costs the buyer
  real money, so local sales close faster.

## Tone

Plain and specific. No marketing language. Short paragraphs. A bulleted
build list reads well on Pinkbike. Mention the reason for selling in one
sentence if it is ordinary (new bike, moved, not riding).

## Posting flow

Each step names the field in the listing frontmatter it fills.

1. Open the URL above in a new tab. Confirm the owner is logged in; if a
   login page appears, stop and ask the owner to log in.
2. Choose the listing category (`category`). For a full bike this is a
   bike category such as Enduro or Trail; the exact list is `unverified`.
3. Fill title (`title`).
4. Fill price (`price`) and currency (`currency`).
5. Fill condition (`condition`).
6. Fill the bike specifics: frame size (`frame_size`), wheel size
   (`wheel_size`), frame material (`frame_material`), front travel
   (`front_travel`), rear travel (`rear_travel`).
7. Fill location: country (`country`), region (`region`), city (`city`).
8. Fill shipping (`shipping`).
9. Paste the description body into the description box.
10. Upload photos from `photos/web/` in manifest order. The first is the
    hero image.
11. Stop. Take a screenshot, tell the owner the form is filled, and wait
    for them to review and click Post.

## Gotchas

- Confirmed 2026-09-28: the post flow starts at
  https://www.pinkbike.com/buysell/selectcategory/ (the "Post New Ad"
  link on /buysell/). /buysell/sell/ is a 404.
- The account must have a country set in its Pinkbike profile before it
  can post. Otherwise selectcategory redirects to /system/message/ with
  "You have not set a valid country in your Profile". Setting it is an
  account settings change, so ask the owner before touching it.
