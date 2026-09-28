---
name: prep-photos
description: Use when raw photos have been dropped into items/<slug>/photos/raw/ and the owner needs them ordered, captioned, resized, and stripped of metadata for a listing. Writes the manifest and runs the photos command.
---

# Prep photos

Turns `photos/raw/` into ordered `photos/web/` JPEGs via the manifest.
Expects status `draft` or later. Leaves status unchanged.

## Gate

Run `uv run classifieds validate items/<slug>`. Stop on any problem.
Then list `photos/raw/`. If it is empty, tell the owner where to put the
photos and stop.

## Choose the order

Read the target marketplace profile in `marketplaces/<name>.md` (ask which
one if not given; default pinkbike for bikes). Note its `photo_max` and
what its "What buyers care about" section says to show.

View every raw photo with the Read tool. For each, note what it shows and
whether it is sharp and well lit. Then propose an order:

1. Hero: the whole item, side-on, best light, clean background. For a bike
   this is the drive side.
2. The other side.
3. Detail shots of the parts buyers ask about, in the order the profile
   lists them.
4. Every flaw the item sheet's "Condition and wear" section mentions.
   Buyers trust listings that show the damage.
5. Extras included.

Drop photos that are blurry, redundant, or show nothing a buyer needs.
Stay at or under `photo_max`. Show the owner the proposed list with one
line per photo and ask for changes before writing anything.

## Write the manifest

Rewrite the table in `photos/manifest.md`. Web names are `NN-descriptor.jpg`
with two digits, a dash, and a short lowercase slug: `01-hero.jpg`,
`02-non-drive-side.jpg`, `03-fork.jpg`. Captions are one short phrase.

## Build and check

Run `uv run classifieds photos items/<slug>`. Every row should print
`written` the first time. Open two or three results with the Read tool
and confirm they are upright and cropped as expected. If a photo needs
cropping, tell the owner which one and why; do not edit raw files.

Finish by stating how many web photos exist and which is the hero.
