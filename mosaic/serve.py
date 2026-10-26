"""Minimal self-hosted server for the static web app (standard library only)."""

import functools
import http.server

from . import SITE_DATA_DIR, SITE_DIR


class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map,
        ".js": "text/javascript",
        ".json": "application/json",
        ".svg": "image/svg+xml",
    }

    def end_headers(self):
        if self.path.startswith("/data/"):
            self.send_header("Cache-Control", "public, max-age=3600")
        super().end_headers()


def main(args):
    if args.rebuild or not (SITE_DATA_DIR / "venues.json").exists():
        from .build import build

        build()
    handler = functools.partial(Handler, directory=str(SITE_DIR))
    with http.server.ThreadingHTTPServer((args.host, args.port), handler) as httpd:
        print(f"MOSAIC running at http://{args.host}:{args.port}/  (Ctrl+C to stop)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
    return 0
