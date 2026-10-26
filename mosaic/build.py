"""Build ``site/data/venues.json`` from the raw files in ``data/raw/``.

Inputs (all optional except at least one SCImago CSV):
  data/raw/scimago/*.csv          SCImago exports (full database and/or per area)
  data/raw/core/conferences.csv   CORE conference ranking export
  data/raw/core/journals.csv      CORE journal ranking export
  data/raw/core/meta.json         CORE editions
  data/raw/openalex/sources.json  OpenAlex enrichment cache
"""

import csv
import json
import re
import time
from collections import Counter, defaultdict

from . import RAW_DIR, SITE_DATA_DIR
from .fields import SCIMAGO_AREAS, for_name, for_to_scimago
from .matching import match_conferences, normalize_issn

TYPE_CODES = {
    "journal": "j",
    "conference and proceedings": "p",
    "book series": "k",
    "trade journal": "t",
}
CORE_ORDER = {"A*": 1, "A": 2, "B": 3, "C": 4}
CATEGORY_RE = re.compile(r"^(.*?)(?:\s*\((Q[1-4])\))?$")


def _read_text(path):
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue


def _num(value, cast=float):
    value = (value or "").strip().replace(",", ".")
    if not value or value == "-":
        return None
    try:
        return cast(value)
    except ValueError:
        return None


def _quartile(value):
    value = (value or "").strip()
    return int(value[1]) if re.fullmatch(r"Q[1-4]", value) else 0


def _split(value):
    return [x.strip() for x in (value or "").split(";") if x.strip()]


# ------------------------------------------------------------------ SCImago

def load_scimago():
    """Read and merge every SCImago CSV. Returns ({sourceid: record}, info)."""
    files = sorted((RAW_DIR / "scimago").glob("*.csv"))
    if not files:
        raise SystemExit(
            "No SCImago CSV found in data/raw/scimago/. "
            "Run `python -m crossfield fetch --scimago` or download it from a browser (see README)."
        )
    parsed = []
    for path in files:
        rows = list(csv.reader(_read_text(path).splitlines(), delimiter=";"))
        header = rows[0]
        year = next((int(m.group(1)) for h in header if (m := re.match(r"Total Docs\. \((\d{4})\)", h))), 0)
        parsed.append((path, year, header, rows[1:]))

    year = max(p[1] for p in parsed)
    records, used_files = {}, []
    for path, fyear, header, rows in parsed:
        if fyear != year:
            print(f"[build] skipping {path.name}: year {fyear}, newest data is {year}")
            continue
        used_files.append(path.name)
        col = {}
        for i, h in enumerate(header):
            col.setdefault(h, i)  # 'Publisher' appears twice; keep the first
        get = lambda row, name: row[col[name]] if name in col and col[name] < len(row) else ""
        for row in rows:
            if len(row) < 5:
                continue
            sid = get(row, "Sourceid").strip()
            if not sid or sid in records:
                continue
            cats = []
            for c in _split(get(row, "Categories")):
                name, q = CATEGORY_RE.match(c).groups()
                cats.append((name.strip(), _quartile(q)))
            records[sid] = {
                "id": sid,
                "title": get(row, "Title").strip(),
                "type": get(row, "Type").strip().lower(),
                "issn": [i for i in (normalize_issn(x) for x in get(row, "Issn").split(",")) if i],
                "publisher": get(row, "Publisher").strip(),
                "oa": get(row, "Open Access").strip() == "Yes",
                "oad": get(row, "Open Access Diamond").strip() == "Yes",
                "sjr": _num(get(row, "SJR")),
                "q": _quartile(get(row, "SJR Best Quartile")),
                "h": _num(get(row, "H index"), int),
                "country": get(row, "Country").strip(),
                "coverage": get(row, "Coverage").strip(),
                "cats": cats,
                "areas": _split(get(row, "Areas")),
            }
        print(f"[build] {path.name}: {len(rows)} rows")
    return records, {"year": year, "files": used_files}


def category_areas(records):
    """Assign every SCImago category to its subject area.

    A source listing category C must list C's area, so the area is the
    intersection of the area lists of all sources in C. Ties (possible when
    the data covers only some areas) are broken by the "X (miscellaneous)"
    naming rule, then by preferring the least frequent area.
    """
    area_freq = Counter(a for r in records.values() for a in r["areas"])
    inter = {}
    for r in records.values():
        areas = set(r["areas"])
        for name, _ in r["cats"]:
            inter[name] = inter[name] & areas if name in inter else set(areas)

    mapping, ambiguous = {}, []
    for cat, cands in inter.items():
        misc = cat.replace(" (miscellaneous)", "")
        if misc in SCIMAGO_AREAS:
            mapping[cat] = misc
        elif cat in SCIMAGO_AREAS:  # "Multidisciplinary"
            mapping[cat] = cat
        elif len(cands) == 1:
            mapping[cat] = next(iter(cands))
        elif cands:
            mapping[cat] = min(cands, key=lambda a: (area_freq[a], a))
            ambiguous.append(cat)
    if ambiguous:
        print(f"[build] {len(ambiguous)} categories assigned by frequency tie-break "
              f"(expected with partial data): {', '.join(sorted(ambiguous)[:8])}...")
    return mapping


# --------------------------------------------------------------------- CORE

def load_core():
    base = RAW_DIR / "core"
    meta = json.loads((base / "meta.json").read_text(encoding="utf-8")) if (base / "meta.json").exists() else {}
    confs, jnls = [], []
    if (base / "conferences.csv").exists():
        for row in csv.reader(_read_text(base / "conferences.csv").splitlines()):
            if len(row) < 6 or not row[0].isdigit():
                continue
            confs.append({
                "id": row[0], "title": row[1].strip(), "acronym": row[2].strip(),
                "source": row[3], "rank": row[4].strip(),
                "for": [f.strip() for f in row[6:9] if f.strip()],
            })
    if (base / "journals.csv").exists():
        for row in csv.DictReader(_read_text(base / "journals.csv").splitlines()):
            jnls.append({
                "id": row["id"], "title": row["title"].strip(), "acronym": "",
                "source": row["source"], "rank": row["rank"].strip(),
                "for": [row[k].strip() for k in ("for1", "for2", "for3") if row.get(k, "").strip()],
                "issn": [i for i in (normalize_issn(row.get(k, "")) for k in ("ISSN1", "ISSN2", "ISSN3", "ISSN4")) if i],
            })
    return confs, jnls, meta


def _core_rank_label(rank):
    r = rank.strip()
    low = r.lower()
    if r in CORE_ORDER:
        return r
    if "not primarily" in low:
        return "Not primarily CS"
    if "survey" in low:
        return "Survey/review"
    if low in ("not ranked", "unranked"):
        return "Unranked"
    return r


def _core_info(entry, kind):
    label = _core_rank_label(entry["rank"])
    info = {"k": label, "o": CORE_ORDER.get(label, 9), "i": entry["id"], "d": kind,
            "f": [for_name(f) for f in entry["for"]], "e": entry["source"]}
    if entry.get("acronym"):
        info["n"] = entry["acronym"]
    return info


# -------------------------------------------------------------------- build

def build(out_dir=SITE_DATA_DIR):
    t0 = time.time()
    records, sinfo = load_scimago()
    cat_area = category_areas(records)
    confs, jnls, core_meta = load_core()

    oa_path = RAW_DIR / "openalex" / "sources.json"
    openalex = json.loads(oa_path.read_text(encoding="utf-8")) if oa_path.exists() else {}

    # --- CORE -> SCImago links
    by_issn = {}
    for sid, r in records.items():
        for i in r["issn"]:
            by_issn.setdefault(i, sid)
    core_of = {}  # scimago id -> core info
    unmatched = []
    for j in jnls:
        sid = next((by_issn[i] for i in j["issn"] if i in by_issn), None)
        if sid and sid not in core_of:
            core_of[sid] = _core_info(j, "j")
        else:
            unmatched.append((j, "j"))
    overrides = {}
    ov_path = RAW_DIR.parent / "core_overrides.json"
    if ov_path.exists():
        overrides = json.loads(ov_path.read_text(encoding="utf-8")).get("conferences", {})
    by_title = {r["title"]: sid for sid, r in records.items()}
    conf_links = {}
    for c in confs:
        if c["acronym"] in overrides and by_title.get(overrides[c["acronym"]]) not in (None, *core_of):
            conf_links[c["id"]] = by_title[overrides[c["acronym"]]]
    taken = set(conf_links.values()) | set(core_of)
    sc_confs = [{"id": sid, "title": r["title"]} for sid, r in records.items()
                if r["type"] == "conference and proceedings" and sid not in taken]
    conf_links.update(match_conferences(
        [c for c in confs if c["acronym"] not in overrides], sc_confs))
    for c in confs:
        sid = conf_links.get(c["id"])
        if sid:
            core_of[sid] = _core_info(c, "c")
        else:
            unmatched.append((c, "c"))

    # --- vocabularies
    areas = sorted({a for r in records.values() for a in r["areas"]} | set(cat_area.values()))
    for c, _ in unmatched:
        for f in c["for"]:
            areas.extend(a for a, _ in for_to_scimago(f) if a not in areas)
    areas = sorted(set(areas))
    area_idx = {a: i for i, a in enumerate(areas)}

    cat_names = set(cat_area)
    for c, _ in unmatched:
        for f in c["for"]:
            for a, cat in for_to_scimago(f):
                if cat and cat not in cat_names:
                    cat_area[cat] = a
                    cat_names.add(cat)
    cats = sorted(cat_names)
    cat_idx = {c: i for i, c in enumerate(cats)}

    topic_freq = Counter(t for v in openalex.values() if v for t in v["t"])
    topics = [t for t, _ in topic_freq.most_common()]
    topic_idx = {t: i for i, t in enumerate(topics)}

    # --- venues
    venues = []
    for sid, r in records.items():
        v = {
            "i": f"s{sid}",
            "t": r["title"],
            "y": TYPE_CODES.get(r["type"], "j"),
            "k": [[cat_idx[n], q] for n, q in r["cats"] if n in cat_idx],
            "a": sorted({area_idx[a] for a in r["areas"] if a in area_idx}),
        }
        if r["issn"]:
            v["s"] = [f"{i[:4]}-{i[4:]}" for i in r["issn"]]
        if r["publisher"]:
            v["p"] = r["publisher"]
        if r["country"]:
            v["c"] = r["country"]
        if r["oa"]:
            v["o"] = 2 if r["oad"] else 1
        if r["sjr"] is not None:
            v["j"] = r["sjr"]
        if r["q"]:
            v["q"] = r["q"]
        if r["h"] is not None:
            v["h"] = r["h"]
        if r["coverage"]:
            v["v"] = r["coverage"]
        if sid in core_of:
            v["r"] = core_of[sid]
        oa = openalex.get(sid)
        if oa:
            if oa.get("u"):
                v["u"] = oa["u"]
            if oa.get("t"):
                v["x"] = [topic_idx[t] for t in oa["t"]]
        venues.append(v)

    for c, kind in unmatched:
        pairs = [p for f in c["for"] for p in for_to_scimago(f)]
        if not pairs:
            continue
        v = {
            "i": f"c{kind}{c['id']}",
            "t": c["title"],
            "y": "p" if kind == "c" else "j",
            "k": sorted({(cat_idx[cat], 0) for _, cat in pairs if cat}),
            "a": sorted({area_idx[a] for a, _ in pairs}),
            "r": _core_info(c, kind),
            "m": 1,
        }
        v["k"] = [list(x) for x in v["k"]]
        if c.get("issn"):
            v["s"] = [f"{i[:4]}-{i[4:]}" for i in c["issn"]]
        venues.append(v)

    # Which areas are fully covered? With a partial download (e.g. one area
    # file), every source shares that area: the UI warns about it.
    area_count = Counter(a for v in venues if not v.get("m") for a in v["a"])
    n_sc = len(records)
    pivots = [areas[a] for a, n in area_count.items() if n == n_sc]

    data = {
        "meta": {
            "built": time.strftime("%Y-%m-%d"),
            "scimago": {"year": sinfo["year"], "files": sinfo["files"], "sources": n_sc},
            "core": {
                "conferences": core_meta.get("conferences", {}).get("source"),
                "journals": core_meta.get("journals", {}).get("source"),
                "linked": len(core_of),
                "core_only": sum(1 for v in venues if v.get("m")),
            },
            "openalex": sum(1 for v in openalex.values() if v),
            "partial": n_sc < 20000,
            "pivots": pivots,
        },
        "areas": [{"n": a, "c": SCIMAGO_AREAS.get(a)} for a in areas],
        "cats": [{"n": c, "a": area_idx[cat_area[c]]} for c in cats],
        "topics": topics,
        "venues": venues,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "venues.json"
    out.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(
        f"[build] {len(venues)} venues ({n_sc} SCImago, {data['meta']['core']['core_only']} CORE-only, "
        f"{len(core_of)} SCImago linked to CORE), {len(areas)} areas, {len(cats)} categories, "
        f"{len(topics)} topics -> {out.relative_to(out_dir.parent.parent)} "
        f"({out.stat().st_size // 1024} KB, {time.time() - t0:.1f}s)"
    )
    return data


def main(args):
    build()
    return 0
