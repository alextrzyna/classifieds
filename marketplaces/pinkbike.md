---
name: Pinkbike BuySell
url: https://www.pinkbike.com/buysell/selectcategory/
title_max: 54
description_max: 5000
photo_max: 12
photo_min_px: 800
fee_rate: 0.0
required_fields:
  - title
  - price
  - currency
  - category
  - year
  - condition
  - frame_size
  - frame_material
  - wheel_size
  - front_travel
  - rear_travel
  - price_offer
  - trades
  - shipping
  - seller_type
field_options:
  category: [XC / Cross Country Bikes, Trail Bikes, Enduro Bikes, Downhill Bikes, Dirt Jump Bikes, Kids Bikes, Vintage Bikes, Enduro Frames, Trail Frames]
  currency: [USD $, CAD $, GBP £, EUR €]
  condition: [New - Unridden/With Tags, Excellent - Lightly Ridden, "Good - Used, Mechanically Sound", Poor - Needs Servicing, For Parts - Not Working / Unrideable]
  frame_size: [XS, S, M, L, XL, XXL, Unknown]
  frame_material: [Aluminium, Carbon Fiber, Chromoly, Steel, Titanium, Unknown]
  wheel_size: ["26\"", "27.5\" / 650B", "29\"", "Mullet 29\"/27.5\"", Unknown]
  front_travel: [0 mm (Rigid), 100 mm, 110 mm, 120 mm, 130 mm, 140 mm, 150 mm, 160 mm, 170 mm, 180 mm, 190 mm, 200 mm, Unknown]
  rear_travel: [0 mm (Hardtail), 100 mm, 110 mm, 120 mm, 130 mm, 135 mm, 140 mm, 143 mm, 145 mm, 150 mm, 153 mm, 155 mm, 160 mm, 170 mm, 180 mm, Unknown]
  price_offer: [Firm, Reasonable offers only, Any offer]
  trades: [No Trades, Will consider bike related trade, Will consider any Trade]
  shipping: [Local pickup only, Will ship locally only, Will ship within country only, Will ship within continent only, Will ship globally]
  seller_type: [Business, Private Seller]
---
# Pinkbike BuySell

Pinkbike is the main used-bike market for mountain bikers in North America.
Buyers are enthusiasts who know the parts and will ask about them. Listings
that get replies show the drive side clearly, state the frame size early,
and list the build honestly, including wear.

Frontmatter fields and options were read from the live form on
2026-09-28 (Enduro Bikes category). Nine 2048px photos (3.2 MB total)
uploaded in one batch without complaint; `photo_max`, `photo_min_px`,
and `description_max` are still `unverified` as hard limits. Travel dropdowns only list the
values above; pick the nearest (Ripmo V2's 147 mm rear -> 145 mm).

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
2. Click the category link (`category`), e.g. "Enduro Bikes" under
   Complete Mountain Bikes. That opens /buysell/newad/?category=<id>.
3. The form is all dropdowns plus title, price, and description. Use
   read_page with the interactive filter to get refs, then form_input.
   Fill: year (`year`), title (`title`, 54 chars max), condition,
   frame_size, frame_material, wheel_size, front_travel, rear_travel,
   price (`price`) and currency (`currency`), price_offer, trades,
   shipping, seller_type.
4. Location is not on the form; it comes from the account profile.
5. Paste the description body into the description box.
6. Upload photos from `photos/web/` in manifest order. The first is the
   hero image. Where in the flow the photo uploader appears is
   `unverified`; it may be after "Save a private draft".
7. After the upload finishes Pinkbike returns to /buysell/edit/?ad=<id>
   with everything intact and the first photo marked "main photo".
   Stop. Take a screenshot, tell the owner the form is filled, and wait
   for them to review and click "Save & Publish".
8. The live ad is at https://www.pinkbike.com/buysell/<id>/ and shows
   "<year> <title>". Sellers get "Mark SOLD", "Edit", "Repost" buttons on
   their own ad; Repost bumps it to the top of search.

## Gotchas

- Confirmed 2026-09-28: the post flow starts at
  https://www.pinkbike.com/buysell/selectcategory/ (the "Post New Ad"
  link on /buysell/). /buysell/sell/ is a 404.
- The account must have a country set in its Pinkbike profile before it
  can post. Otherwise selectcategory redirects to /system/message/ with
  "You have not set a valid country in your Profile". Setting it is an
  account settings change, so ask the owner before touching it. The
  profile edit page is /u/<username>/editprofile/; Country, State, and
  City are autocomplete text boxes with a picker, then Save.
- Do not put the year in the title. The form rejects it ("The year will
  be added automatically to title") and Pinkbike prepends the Year
  dropdown value when displaying the ad.
- The Description survives a validation-error reload; dropdowns and
  title do too. Only fix the flagged field and resubmit.
- "Save & Upload Photos" saves a private draft and opens the uploader.
  That is the only way to add photos from disk.
- First-time posters must pass a one-time SMS phone verification
  (/buysell/smsverify/). The owner does this themselves: never enter
  their phone number, and the code goes to their phone.
