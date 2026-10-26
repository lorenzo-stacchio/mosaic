"""MOSAIC (Multidisciplinary Outlet Search Across Indexed Categories): find journals and conferences at the intersection of scientific fields.

Data pipeline (fetch + build) that turns the SCImago Journal Rank and CORE
rankings into a static JSON index consumed by the web app in ``site/``.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
SITE_DIR = ROOT / "site"
SITE_DATA_DIR = SITE_DIR / "data"

__version__ = "1.0.0"
