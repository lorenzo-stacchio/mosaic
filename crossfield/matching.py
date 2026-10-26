"""Link CORE entries to SCImago sources.

Journals are matched on ISSN. Conferences have no identifier in common, so the
CORE title is compared with the titles of SCImago "conference and proceedings"
sources after normalisation ("Proceedings of the IEEE ..." prefixes, publisher
names and stop words removed), using an order-aware token similarity. Two
guards keep false positives out:

* if both titles name the kind of event (conference / symposium / workshop)
  and the kinds differ, they are different events (e.g. ISIT vs ITW);
* if the SCImago title ends with an acronym ("..., MICRO") it must equal the
  CORE acronym.
"""

import re
import unicodedata
from difflib import SequenceMatcher

STOP = set(
    "proceedings proceeding proc of the on and in for a an to at ieee acm annual "
    "international usenix siam ifip acs".split()
)
KINDS = {"conference": "c", "symposium": "s", "workshop": "w"}
TRAILING_ACRONYM = re.compile(r"(?:,|\s-|\s–|\()\s*([A-Z][A-Za-z0-9\-]{1,15})\)?\s*(?:-\s*Proceedings)?\s*$")


def _ascii(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()


def tokens(title):
    """Content tokens of a venue title, plus the set of event kinds it names."""
    s = _ascii(re.sub(r"\(.*?\)", " ", title)).replace("&", " and ").replace("computer society", " ")
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    words = s.split()
    kinds = {KINDS[w] for w in words if w in KINDS}
    toks = [w for w in words if w not in STOP and w not in KINDS and not w.isdigit()]
    return toks, kinds


def trailing_acronym(title):
    m = TRAILING_ACRONYM.search(title)
    if not m:
        return None
    acr = m.group(1)
    # "..., Proceedings" or "..., Networking" are words, not acronyms
    if sum(ch.isupper() for ch in acr) < 2 or acr.upper() == "PROCEEDINGS":
        return None
    return acr.upper()


def normalize_issn(raw):
    raw = raw.strip().upper().replace("-", "")
    return raw if re.fullmatch(r"\d{7}[\dX]", raw) else None


def match_conferences(core_confs, scimago_confs, threshold=0.85):
    """Return {core_id: scimago_id}.

    core_confs: iterable of dicts with keys id, title, acronym.
    scimago_confs: iterable of dicts with keys id, title.
    """
    cands = []
    for s in scimago_confs:
        toks, kinds = tokens(s["title"])
        if toks:
            cands.append((s["id"], toks, set(toks), kinds, trailing_acronym(s["title"])))

    scored = []
    for c in core_confs:
        toks, kinds = tokens(c["title"])
        if not toks:
            continue
        tset, acr = set(toks), (c.get("acronym") or "").upper()
        best = None
        for sid, stoks, sset, skinds, sacr in cands:
            if not tset & sset:
                continue
            if kinds and skinds and not kinds & skinds:
                continue
            if sacr and acr and sacr != acr and sacr not in acr.split("-"):
                continue
            score = SequenceMatcher(None, toks, stoks, autojunk=False).ratio()
            ok = score >= threshold or (sacr and sacr == acr and score >= 0.4)
            if ok and (best is None or score > best[0]):
                best = (score, sid)
        if best:
            scored.append((best[0], c["id"], best[1]))

    # one-to-one: the best-scoring pair wins
    result, used = {}, set()
    for score, cid, sid in sorted(scored, reverse=True):
        if sid not in used:
            result[cid] = sid
            used.add(sid)
    return result
