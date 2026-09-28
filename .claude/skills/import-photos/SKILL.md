---
name: import-photos
description: Use when the owner's photos are on a camera or SD card plugged into this Mac and need to land in items/<slug>/photos/raw/. Detects the mounted card, shows contact sheets by shooting date, copies the chosen shots with checksum verification, logs the import, and ejects.
---

# Import photos

Copies photos from a mounted camera or card into `items/<slug>/photos/raw/`.
Expects an existing item at any status. Leaves status unchanged. Nothing
here touches the camera's files except to read them.

## Gate

Run `uv run classifieds validate items/<slug>`. Stop on any problem.

## Find the card

Cameras in USB mass-storage mode and SD cards in a reader mount under
`/Volumes`. Find every volume with a `DCIM` folder:

```bash
for v in /Volumes/*/; do [ -d "$v/DCIM" ] && echo "$v"; done
```

Volume names can contain spaces (the Lumix S1II mounts as `LUMIX` and
`LUMIX 1`, one per card slot). Always quote paths.

If nothing is found:

- A Lumix must be set to **PC(Storage)**, not PC(Tether). Ask the owner to
  switch and replug. Then wait with a background `until` loop that polls
  for a `DCIM` folder.
- Cameras that only offer PTP/MTP (most Nikon and Canon bodies) do not
  mount. `gphoto2 --auto-detect` and `gphoto2 --get-all-files` (Homebrew
  `gphoto2`) can pull from those. Close Image Capture and Photos first.
- A phone: the owner AirDrops or exports to a folder and gives the path.

A card can have more than one `DCIM/xxx_YYYY` folder; scan all of them.
Ignore dotfiles and the `PRIVATE/` tree (video metadata).

## Show what is there

Summarise by shooting date and type, then build contact sheets in the
scratchpad (never in the item folder) and view them with the Read tool.
Use the `stat`-free approach below; the GNU `stat` on this Mac's PATH
does not accept macOS flags.

```bash
uv run python - "$SCRATCH/sheets" "/Volumes/<CARD>/DCIM" <<'PY'
import sys
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageDraw, ImageOps
out, D = Path(sys.argv[1]), Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
files = sorted(p for p in D.rglob("*") if p.is_file() and not p.name.startswith(".")
               and p.suffix.upper() in (".JPG", ".JPEG", ".HEIC", ".PNG"))
groups = {}
for p in files:
    groups.setdefault(datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d"), []).append(p)
for day, ps in groups.items(): print(day, len(ps))
TW, TH, COLS = 300, 200, 6
for day, ps in groups.items():
    for chunk in range(0, len(ps), 30):
        sub = ps[chunk:chunk + 30]; rows = (len(sub) + COLS - 1) // COLS
        sheet = Image.new("RGB", (COLS * TW, rows * (TH + 18)), "white"); dr = ImageDraw.Draw(sheet)
        for i, p in enumerate(sub):
            with Image.open(p) as im:
                im.draft("RGB", (TW * 2, TH * 2)); im = ImageOps.exif_transpose(im); im.thumbnail((TW, TH))
                x, y = (i % COLS) * TW, (i // COLS) * (TH + 18); sheet.paste(im, (x + (TW - im.width) // 2, y))
            dr.text((x + 4, y + TH + 2), p.stem, fill="black")
        name = out / f"{day}-{chunk // 30 + 1}.jpg"; sheet.save(name, quality=80); print(name)
PY
```

Ask the owner which date or which frames are the item, or confirm your
own read of the sheets. Raw-only shoots (`.RW2`, `.NEF`, `.CR3`) are not
readable by the photo pipeline; say so and ask for JPEGs.

## Copy and verify

Copy the chosen files, keeping their original names, then compare
checksums against the card:

```bash
RAW=items/<slug>/photos/raw
cp "/Volumes/<CARD>/DCIM/<folder>/<file>" "$RAW/"   # one per chosen file
for f in "$RAW"/*; do
  [ "$(md5 -q "$f")" = "$(md5 -q "/Volumes/<CARD>/DCIM/<folder>/$(basename "$f")")" ] && echo "ok $f" || echo "MISMATCH $f"
done
```

Any MISMATCH: delete that copy and copy it again. Raw files are
gitignored on purpose (they carry GPS and camera metadata); only the
`photos/web/` output is committed.

## Log and eject

Append to `items/<slug>/log.md`:

```
<today>  note  imported <N> raw photos <first>-<last> from <camera> via <how>, shot <date>
```

Commit the log line. Then eject every volume from that device so the
owner can unplug:

```bash
diskutil unmount "/Volumes/<CARD>"
```

Finish by stating the count, the file range, and that the next step is
the prep-photos skill.
