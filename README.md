# MOSAIC

**Multidisciplinary Outlet Search Across Indexed Categories.**
Find the perfect journal for your multidisciplinary team.

**Live:** <https://lorenzo-stacchio.github.io/mosaic/>

MOSAIC helps researchers who work across disciplines (a chemist building
machine-learning models, a historian using quantitative methods) choose venues
that are recognised by *every* community involved. Pick two or more fields from
the SCImago classification and MOSAIC lists the venues indexed in all of
them, with:

- the venue's **quartile in each field you chose** (a journal can be Q1 in
  Computer Science and Q3 in History);
- SJR, best quartile, H-index, citations per document, yearly output,
  publisher, country, open access;
- the **CORE rank** (A*, A, B, C) for computer science venues;
- a one-sentence **profile** of the venue's scope and its SCImago categories;
- links to the **SCImago profile**, the **ISSN record** and the **CORE entry**.

Only venues indexed in SCImago or ranked by CORE are listed. CORE currently
covers computer science only.

It is a static web app: the data is pre-built into one JSON file, so it runs
on **GitHub Pages** with no server, or self-hosted with a single Python command.

## How it works

```text
data/raw/                python -m mosaic build           site/
  scimago/*.csv  ─┐                                         index.html
                  ├──►  merge, link CORE ↔ SCImago  ──►     assets/
  core/*.csv     ─┘                                         data/venues.json
```

- **Fields and intersection.** Each circle in the interface is a *field*: one
  SCImago subject area (e.g. *Chemistry*) or category (e.g. *Organic
  Chemistry*). *Widen* a circle to accept several alternatives (OR). A venue is
  listed when it belongs to every circle (AND); with three or more circles you
  can relax this to "at least k of n".
- **Per-field quartile.** SCImago gives a quartile per category. For each
  circle, MOSAIC shows the best quartile among the venue's categories that
  fall in that circle. The default sort, *Weakest field quartile*, puts first
  the venues that are strong in all your fields at once.
- **CORE ↔ SCImago.** CORE journals are linked by ISSN. CORE conferences are
  linked to SCImago "conference and proceedings" sources by normalised title
  ("Proceedings of the IEEE …" prefixes removed, order-aware token similarity,
  acronym and event-kind checks). Exceptions go in
  [data/core_overrides.json](data/core_overrides.json). CORE venues that are not
  in SCImago are still listed: their ANZSRC field-of-research codes are mapped
  onto SCImago fields ([mosaic/fields.py](mosaic/fields.py)).
- **Profiles** are composed in the browser from SCImago data only (subject
  areas and category quartiles), so they are exact for every venue rather
  than written by hand.
- **Shareable searches.** The whole search lives in the URL, so a link
  reproduces it. Results can be downloaded as CSV.

## Quick start

Requires Python 3.10+, no dependencies.

```bash
python -m mosaic build     # data/raw/ -> site/data/venues.json
python -m mosaic serve     # http://127.0.0.1:8000
```

## Data and yearly update

SCImago publishes a new edition every year (usually in spring); CORE
publishes new conference rankings every few years. To refresh:

1. **SCImago.** scimagojr.com protects downloads with a browser check, so the
   export is downloaded by hand from a browser:
   open <https://www.scimagojr.com/journalrank.php>, keep *All subject areas*
   and *All types*, pick the year and click **Download data**. Save the CSV in
   `data/raw/scimago/` and delete the previous year's files (only the newest
   year is used anyway). You can also add per-area exports: all CSVs in the
   folder are merged. `python -m mosaic fetch --scimago` tries the
   download automatically and prints the exact URLs if it is refused.
2. **CORE**, fully automatic:

   ```bash
   python -m mosaic fetch --core   # newest CORE editions (e.g. ICORE2026, CORE2020)
   ```

3. `python -m mosaic build`, check locally, commit `data/raw/`.

> **Current data:** SCImago 2025 (32,193 sources, all subject areas), CORE
> ICORE2026 conferences and CORE2020 journals.

The workflow [update-data.yml](.github/workflows/update-data.yml) repeats
steps 2–3 every June and opens a pull request; add the SCImago file to that
branch before merging. It needs *Settings → Actions → General → Allow GitHub
Actions to create and approve pull requests*.

## Deploy

### GitHub Pages

1. Push the repository to GitHub.
2. *Settings → Pages → Build and deployment → Source: GitHub Actions*.
3. Every push to `main` runs [pages.yml](.github/workflows/pages.yml): tests,
   build of `site/data/venues.json` from `data/raw/`, deploy.

### Self-hosted

```bash
python -m mosaic serve --host 0.0.0.0 --port 8000
```

or with Docker:

```bash
docker build -t mosaic .
docker run -p 8000:8000 mosaic
```

`site/` is plain static files after the build, so any web server (nginx,
Caddy, S3…) can serve it as well.

## Project layout

| Path | Content |
| --- | --- |
| `mosaic/fetch.py` | Downloads CORE and, when allowed, SCImago data |
| `mosaic/build.py` | Merges the raw data into `site/data/venues.json` |
| `mosaic/matching.py` | CORE ↔ SCImago conference matching |
| `mosaic/fields.py` | SCImago areas, ANZSRC FoR names and FoR → SCImago mapping |
| `site/` | The web app (vanilla HTML, CSS, JS) |
| `data/raw/` | Raw data, versioned |
| `tests/` | `python -m unittest discover -s tests` |

## Credits

MOSAIC was made by [Lorenzo Stacchio](https://lorenzo-stacchio.github.io/),
whose research joins extended reality and artificial intelligence with
cultural heritage, education and the creative industries, and who needed a
way to find venues that several disciplines respect at once.

MOSAIC is built on the [SCImago Journal & Country Rank](https://www.scimagojr.com):
every quartile, SJR value, H-index and subject category comes from SCImago
(SCImago Research Group, Scopus data). If these indicators inform your choice,
please cite SCImago:

> SCImago (n.d.). SJR: SCImago Journal & Country Rank [Portal]. Retrieved
> *date*, from <https://www.scimagojr.com>

Also uses the [CORE Rankings Portal](https://portal.core.edu.au) and links to
the [ISSN Portal](https://portal.issn.org). Code released under the GPL-3.0 license.
