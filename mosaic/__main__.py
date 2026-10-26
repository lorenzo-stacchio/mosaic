"""Command line entry point.

  python -m mosaic fetch --core --openalex   download / refresh raw data
  python -m mosaic build                     build site/data/venues.json
  python -m mosaic serve                     serve the web app locally
"""

import argparse
import sys


def parse_args(argv=None):
    parser = argparse.ArgumentParser(prog="mosaic", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    f = sub.add_parser("fetch", help="download raw data into data/raw/")
    f.add_argument("--core", action="store_true", help="CORE conference and journal rankings")
    f.add_argument("--scimago", action="store_true", help="try to download SCImago exports")
    f.add_argument("--openalex", action="store_true", help="enrich SCImago sources with OpenAlex topics/homepages")
    f.add_argument("--all", action="store_true", help="all of the above")
    f.add_argument("--year", type=int, help="SCImago edition (default: latest)")
    f.add_argument("--per-area", action="store_true", help="also download one SCImago file per subject area")
    f.add_argument("--core-conf-source", help="CORE conference edition, e.g. ICORE2026 (default: latest)")
    f.add_argument("--core-jnl-source", help="CORE journal edition, e.g. CORE2020 (default: latest)")
    f.add_argument("--max-requests", type=int, default=900, help="OpenAlex request budget per run")

    sub.add_parser("build", help="build site/data/venues.json from data/raw/")

    s = sub.add_parser("serve", help="serve site/ (builds the data first if missing)")
    s.add_argument("--host", default="127.0.0.1")
    s.add_argument("--port", type=int, default=8000)
    s.add_argument("--rebuild", action="store_true", help="rebuild the data before serving")

    args = parser.parse_args(argv)
    if args.command == "fetch":
        if args.all:
            args.core = args.scimago = args.openalex = True
        if not (args.core or args.scimago or args.openalex):
            parser.error("choose at least one of --core, --scimago, --openalex, --all")
    return args


def main(argv=None):
    args = parse_args(argv)
    if args.command == "fetch":
        from .fetch import main as run
    elif args.command == "build":
        from .build import main as run
    else:
        from .serve import main as run
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
