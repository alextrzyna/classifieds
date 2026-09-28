"""Command line entry point. All I/O lives here; modules stay pure."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .items import STATUSES, ItemError, load_item, validate_item
from .listings import ListingError, check_listing, load_listing, web_photos
from .photos import PhotoError, load_manifest, process_photos
from .profiles import ProfileError, find_repo_root, load_profile, profile_path
from .status import StatusError, apply_status


def _report(summary: str, problems: list[str]) -> int:
    if not problems:
        print(f"ok: {summary}")
        return 0
    print(f"{summary}: {len(problems)} problem(s)")
    for p in problems:
        print(f"- {p}")
    return 1


def cmd_validate(args: argparse.Namespace) -> int:
    try:
        item = load_item(Path(args.item))
    except ItemError as exc:
        return _report("validate", [str(exc)])
    return _report(f"validate {item.slug}", validate_item(item))


def cmd_photos(args: argparse.Namespace) -> int:
    item_dir = Path(args.item)
    try:
        manifest = load_manifest(item_dir)
        results = process_photos(item_dir, manifest, force=args.force)
    except PhotoError as exc:
        return _report("photos", [str(exc)])
    for name, outcome in results:
        print(f"{name} {outcome}")
    return 0


def cmd_check_listing(args: argparse.Namespace) -> int:
    item_dir = Path(args.item)
    try:
        item = load_item(item_dir)
        root = find_repo_root(item_dir)
        profile = load_profile(profile_path(root, args.marketplace))
        listing = load_listing(item_dir, args.marketplace)
    except (ItemError, ProfileError, ListingError) as exc:
        return _report(f"check-listing {args.marketplace}", [str(exc)])
    problems = check_listing(item, listing, profile, web_photos(item_dir))
    return _report(f"check-listing {item.slug} on {profile.name}", problems)


def cmd_status(args: argparse.Namespace) -> int:
    try:
        item = apply_status(
            Path(args.item), args.new_status, price=args.price, floor=args.floor, note=args.note,
        )
    except (ItemError, StatusError) as exc:
        return _report("status", [str(exc)])
    print(f"ok: {item.slug} is now {item.status}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="classifieds",
        description="Validate items, prepare photos, check listings, and move status.",
    )
    sub = parser.add_subparsers(dest="command", metavar="command")

    p = sub.add_parser("validate", help="check an item folder against the data model")
    p.add_argument("item", help="path to items/<slug>")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("photos", help="build photos/web from photos/raw per the manifest")
    p.add_argument("item")
    p.add_argument("--force", action="store_true", help="rewrite even if up to date")
    p.set_defaults(func=cmd_photos)

    p = sub.add_parser("check-listing", help="check listings/<marketplace>.md against its profile")
    p.add_argument("item")
    p.add_argument("marketplace", help="name of a file in marketplaces/ without .md")
    p.set_defaults(func=cmd_check_listing)

    p = sub.add_parser("status", help="move an item to a new status and log it")
    p.add_argument("item")
    p.add_argument("new_status", choices=STATUSES)
    p.add_argument("--price", type=int, help="set the asking price")
    p.add_argument("--floor", type=int, help="set the private floor")
    p.add_argument("--note", help="text to append to the log entry, e.g. the listing URL")
    p.set_defaults(func=cmd_status)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_usage(sys.stderr)
        return 2
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
