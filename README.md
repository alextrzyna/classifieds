# classifieds

Skills, a small toolkit, and per-item folders for selling things on
online marketplaces with Claude Code.

## Setup

1. Clone this repo and install the toolkit:

   ```
   git clone https://github.com/alextrzyna/classifieds.git
   cd classifieds
   uv sync
   ```

2. Create the private `items/` directory. It holds everything about the
   things you sell (item sheets, photos, floor prices, research, logs)
   and is ignored by this repo, so nothing personal can end up on
   GitHub. By default it becomes its own git repo so you can version
   your item data locally:

   ```
   uv run classifieds init-items
   ```

   Add `--no-git` if you'd rather have a plain folder. Either way, raw
   photos are ignored (they carry GPS and camera metadata); only the
   generated `photos/web/` JPEGs are versioned.

3. Install the [Claude in Chrome](https://claude.ai/chrome) extension
   and log into the marketplace you'll sell on. Claude fills sell forms
   in your own logged-in browser and never clicks Post.

## Selling something

1. Start a Claude Code session in this repo and say what you want to
   sell. The `sell-item` skill walks the steps:
   new-item, prep-photos, price-research, write-listing, post-listing.
2. Put photos from your phone or camera in `items/<slug>/photos/raw/`
   (the `import-photos` skill pulls them off a mounted card). HEIC is
   fine. Raw photos are never committed (they carry GPS and camera
   metadata); the generated `photos/web/` JPEGs, with metadata stripped,
   are what get committed and uploaded.
3. Claude fills the marketplace's sell form in your logged-in Chrome.
   You review and click Post.

## Layout

- `items/<slug>/` one folder per item: `item.md`, `photos/`, `research/`,
  `listings/`, `log.md`. Private, ignored by this repo, created by
  `classifieds init-items` (see Setup). Commit changes there with
  `git -C items ...`.
- `marketplaces/` one profile per marketplace with form limits and the
  posting flow.
- `.claude/skills/` the skills.
- `tools/` the Python toolkit and tests.

## Toolkit

```
uv sync
uv run pytest
uv run classifieds init-items [--no-git]
uv run classifieds validate items/<slug>
uv run classifieds photos items/<slug> [--force]
uv run classifieds check-listing items/<slug> <marketplace>
uv run classifieds status items/<slug> <draft|priced|listed|sold|withdrawn> [--price N] [--floor N] [--note TEXT]
```

Status moves: draft -> priced -> listed -> sold or withdrawn. A listed or
withdrawn item can go back to priced for re-pricing.

## Privacy

The floor price is private. It lives in `item.md`, the research file, and
`log.md`. `check-listing` fails if it appears in listing text. The
"Private notes" section of `item.md` is never copied into a listing.

## License

MIT. See `LICENSE`.
