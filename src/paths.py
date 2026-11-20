"""Repository paths. Nothing outside this repository is referenced."""
from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(os.environ.get("SOURCEMAP_PROJECT_ROOT", "/content/drive/MyDrive/SourceMap_Research"))
REPO_ROOT = Path(os.environ.get("SOURCEMAP_REPO_ROOT", str(PROJECT_ROOT / "sourcemap-research")))

DATA = REPO_ROOT / "data"                 # PDFs and other downloads; never committed
DATA_SURVEYS = DATA / "surveys"
DATA_DEFENCES = DATA / "defences"
DATA_MANUSCRIPT = DATA / "manuscript"
REPORTS = REPO_ROOT / "reports"
RECORDS = REPORTS / "records"             # one YAML file per report read
FIGURES = REPO_ROOT / "figures"
TABLES = REPO_ROOT / "tables"
SCHEMA = REPO_ROOT / "schema"
NOTEBOOKS = REPO_ROOT / "notebooks"


def ensure_dirs() -> None:
    for folder in (DATA_SURVEYS, DATA_DEFENCES, DATA_MANUSCRIPT, RECORDS, FIGURES, TABLES, SCHEMA):
        folder.mkdir(parents=True, exist_ok=True)
