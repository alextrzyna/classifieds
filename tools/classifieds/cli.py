"""Command line entry point. All I/O lives here; modules stay pure."""
from __future__ import annotations

import argparse
import sys


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="classifieds",
        description="Validate items, prepare photos, check listings, and move status.",
    )
    parser.add_subparsers(dest="command", metavar="command")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_usage(sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
