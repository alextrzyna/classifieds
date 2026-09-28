# CLAUDE.md

This repo sells items on online marketplaces. Read `README.md` first.

## Rules

- Run `uv run classifieds validate items/<slug>` before and after changing
  any item. Skills gate on it.
- Never put the floor or the Private notes section into a listing.
- Never click Post, Publish, or List on a marketplace. The owner submits.
- The toolkit in `tools/` never generates prose and never uses the
  network. Prose and research belong to the skills.
- Marketplace profiles are ground truth for form fields. When a live form
  differs, fix the profile and note it under Gotchas.
- Dates in frontmatter are `YYYY-MM-DD`. Prices are whole currency units.

## Testing

`uv run pytest`. Tests live in `tools/tests/`. Real items and profiles
are validated by `test_real_items.py` and `test_real_profiles.py`, so a
broken item.md fails the suite.
