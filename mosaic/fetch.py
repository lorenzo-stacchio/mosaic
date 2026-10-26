"""Download raw data into ``data/raw/``.

* CORE (portal.core.edu.au): conference and journal rankings, CSV export.
* SCImago (scimagojr.com): the whole database plus one file per subject area.
  scimagojr.com sits behind a browser challenge, so automated downloads are
  often refused; in that case the files must be downloaded from a browser and
  dropped into ``data/raw/scimago/`` (see README).
"""

import csv
import io
import json
import re
import time
import urllib.error
import urllib.request

from . import RAW_DIR
from .fields import SCIMAGO_AREAS

USER_AGENT = "mosaic-data-fetcher/1.0 (+https://github.com/; academic venue finder)"

CORE_BASE = "https://portal.core.edu.au"
SCIMAGO_BASE = "https://www.scimagojr.com/journalrank.php"


def _get(url, ua=USER_AGENT, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": ua})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


# --------------------------------------------------------------------- CORE

def _latest_core_source(kind):
    """Read the source selector of the CORE portal and return the newest edition."""
    html = _get(f"{CORE_BASE}/{kind}/").decode("utf-8", "replace")
    sources = re.findall(r'<option value="((?:I?CORE|ERA)\d{4})"', html)
    if not sources:
        raise RuntimeError(f"Cannot find CORE editions on {CORE_BASE}/{kind}/")
    return max(sources, key=lambda s: int(s[-4:]))


def fetch_core(conf_source=None, jnl_source=None):
    out = RAW_DIR / "core"
    out.mkdir(parents=True, exist_ok=True)
    meta = {}
    for kind, name, source in (
        ("conf-ranks", "conferences", conf_source),
        ("jnl-ranks", "journals", jnl_source),
    ):
        source = source or _latest_core_source(kind)
        url = f"{CORE_BASE}/{kind}/?search=&by=all&source={source}&sort=arank&page=1&do=Export"
        print(f"[core] {name}: {source}")
        data = _get(url)
        rows = list(csv.reader(io.StringIO(data.decode("utf-8", "replace"))))
        if len(rows) < 10:
            raise RuntimeError(f"CORE export for {source} looks empty ({len(rows)} rows)")
        (out / f"{name}.csv").write_bytes(data)
        meta[name] = {"source": source, "rows": len(rows), "fetched": time.strftime("%Y-%m-%d")}
        print(f"[core]   {len(rows)} rows -> data/raw/core/{name}.csv")
    (out / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")


# ------------------------------------------------------------------ SCImago

def scimago_urls(year=None):
    """All SCImago export URLs: the full database, then one per subject area."""
    q = f"&year={year}" if year else ""
    urls = [("all", f"{SCIMAGO_BASE}?out=xls{q}")]
    for area, code in SCIMAGO_AREAS.items():
        urls.append((area, f"{SCIMAGO_BASE}?area={code}&out=xls{q}"))
    return urls


def fetch_scimago(year=None, per_area=False):
    """Try to download SCImago exports. Returns True on success.

    Only plain HTTP requests are made; if the site answers with its browser
    challenge, the manual procedure is printed instead.
    """
    out = RAW_DIR / "scimago"
    out.mkdir(parents=True, exist_ok=True)
    targets = scimago_urls(year)
    if not per_area:
        targets = targets[:1]
    ok = True
    for name, url in targets:
        fname = "scimagojr_all.csv" if name == "all" else f"scimagojr_area_{SCIMAGO_AREAS[name]}.csv"
        try:
            data = _get(url, timeout=180)
            if not data.startswith(b"Rank;"):
                raise RuntimeError("response is not a SCImago CSV export")
            (out / fname).write_bytes(data)
            print(f"[scimago] {name}: {len(data) // 1024} KB -> data/raw/scimago/{fname}")
        except (urllib.error.HTTPError, urllib.error.URLError, RuntimeError, TimeoutError) as exc:
            print(f"[scimago] {name}: download refused ({exc})")
            ok = False
            break
        time.sleep(2)
    if not ok:
        print(
            "\n[scimago] scimagojr.com requires a real browser. Download manually:\n"
            "  1. open https://www.scimagojr.com/journalrank.php in your browser\n"
            "  2. leave 'All subject areas' and 'All types', choose the year,\n"
            "     click 'Download data' (or open the URL below in the same browser):\n"
            f"       {targets[0][1]}\n"
            "  3. save the CSV into data/raw/scimago/ (any file name ending in .csv)\n"
            "  Optional, per-area files (merged automatically by the build):"
        )
        for name, url in scimago_urls(year)[1:]:
            print(f"       {name:<46} {url}")
    return ok


def main(args):
    if args.core:
        fetch_core(args.core_conf_source, args.core_jnl_source)
    if args.scimago:
        fetch_scimago(args.year, per_area=args.per_area)
    return 0
