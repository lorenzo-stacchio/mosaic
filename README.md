# Crossfield

**Find journals and conferences that count in more than one scientific field.**

Crossfield helps researchers who work across disciplines (a chemist building
machine-learning models, a historian using quantitative methods) choose venues
that are recognised by *every* community involved. Pick two or more fields from
the SCImago classification and Crossfield lists the venues indexed in all of
them, with:

- the venue's **quartile in each field you chose** (a journal can be Q1 in
  Computer Science and Q3 in History);
- SJR, best quartile, H-index, publisher, country, open access;
- the **CORE rank** (A*, A, B, C) for computer science venues;
- **main topics**: SCImago categories plus research topics from OpenAlex;
- links to the **SCImago profile**, the venue's **website** and its **CORE entry**.

Only venues indexed in SCImago or ranked by CORE are listed. CORE currently
covers computer science only.

It is a static web app: the data is pre-built into one JSON file, so it runs
on **GitHub Pages** with no server, or self-hosted with a single Python command.

## How it works

```text
data/raw/                     python -m crossfield build        site/
  scimago/*.csv   ─┐                                             index.html
  core/*.csv      ─┼──►  merge, link CORE↔SCImago, enrich  ──►   assets/
  openalex/*.json ─┘                                             data/venues.json
```

- **Fields and intersection.** Each circle in the interface is a *field*: one
  SCImago subject area (e.g. *Chemistry*) or category (e.g. *Organic
  Chemistry*). *Widen* a circle to accept several alternatives (OR). A venue is
  listed when it belongs to every circle (AND); with three or more circles you
  can relax this to "at least k of n".
- **Per-field quartile.** SCImago gives a quartile per category. For each
  circle, Crossfield shows the best quartile among the venue's categories that
  fall in that circle. The default sort, *Weakest field quartile*, puts first
  the venues that are strong in all your fields at once.
- **CORE ↔ SCImago.** CORE journals are linked by ISSN. CORE conferences are
  linked to SCImago "conference and proceedings" sources by normalised title
  ("Proceedings of the IEEE …" prefixes removed, order-aware token similarity,
  acronym and event-kind checks). Exceptions go in
  [data/core_overrides.json](data/core_overrides.json). CORE venues that are not
  in SCImago are still listed: their ANZSRC field-of-research codes are mapped
  onto SCImago fields ([crossfield/fields.py](crossfield/fields.py)).
- **Topics and websites** come from [OpenAlex](https://openalex.org), looked up
  by ISSN and cached in `data/raw/openalex/sources.json`.
- **Shareable searches.** The whole search lives in the URL, so a link
  reproduces it. Results can be downloaded as CSV.

## Quick start

Requires Python 3.10+, no dependencies.

```bash
python -m crossfield build     # data/raw/ -> site/data/venues.json
python -m crossfield serve     # http://127.0.0.1:8000
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
   folder are merged. `python -m crossfield fetch --scimago` tries the
   download automatically and prints the exact URLs if it is refused.
2. **CORE and OpenAlex**, fully automatic:

   ```bash
   python -m crossfield fetch --core       # newest CORE editions (e.g. ICORE2026, CORE2020)
   python -m crossfield fetch --openalex   # topics + websites, incremental and cached
   ```

   OpenAlex allows about 1,000 requests a day without a key, enough for the
   full SCImago database (~300 requests). Set `OPENALEX_API_KEY` for more.
3. `python -m crossfield build`, check locally, commit `data/raw/`.

> **Current data.** The repository ships the SCImago 2024 *Computer Science*
> export only, so every search currently includes Computer Science (the app
> shows a notice). Add the full SCImago export as in step 1 to search any
> combination, e.g. History × Mathematics.

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
python -m crossfield serve --host 0.0.0.0 --port 8000
```

or with Docker:

```bash
docker build -t crossfield .
docker run -p 8000:8000 crossfield
```

`site/` is plain static files after the build, so any web server (nginx,
Caddy, S3…) can serve it as well.

## Project layout

| Path | Content |
| --- | --- |
| `crossfield/fetch.py` | Downloads CORE, SCImago (when allowed) and OpenAlex data |
| `crossfield/build.py` | Merges the raw data into `site/data/venues.json` |
| `crossfield/matching.py` | CORE ↔ SCImago conference matching |
| `crossfield/fields.py` | SCImago areas, ANZSRC FoR names and FoR → SCImago mapping |
| `site/` | The web app (vanilla HTML, CSS, JS) |
| `data/raw/` | Raw data, versioned |
| `tests/` | `python -m unittest discover -s tests` |
| `main.py`, `configs/` | The original command-line scraper (below) |

## Legacy command-line scraper

`main.py` filters one SCImago export (Computer Science, hard-coded in
`pivot_area_code`) by the areas and categories listed in a config file and
writes CSV/XLSX files to `outs/`. Needs `pip install -r requirements.txt`.

```bash
python main.py --config configs/example_macro.json
python main.py --config configs/example_macro_micro.json
python main.py --config "configs/social science.json" --sub_area_computer_science_code 1702
```

## Credits

Data from [SCImago Journal & Country Rank](https://www.scimagojr.com)
(SCImago, Elsevier Scopus), the [CORE Rankings Portal](https://portal.core.edu.au)
and [OpenAlex](https://openalex.org) (CC0). Please cite SCImago and CORE when
you use their rankings. Code released under the GPL-3.0 license.
