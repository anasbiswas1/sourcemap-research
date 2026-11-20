# Who told the model? A review of defences against indirect prompt injection

Working repository for a review paper by Md Anas Biswas (School of Computing, University of Portsmouth).

An assistant that reads a web page, an e-mail or a tool result for its user can be hijacked by an instruction hidden in that text. Many defences have been published. This project reads them through one question: who told the model which text is an instruction and which is data? For every published defence it records how the source of an instruction is shown to the model, how the defensive behaviour was built, and what the paper's own evaluation shows about three jobs: resisting the injected instruction, doing the user's task, and handling the document's text correctly. It also grades every comparative claim by how well its conditions were matched.

There are no new experiments here. Every number in `reports/` is a published number with the paper and page it was read from.

## Status

Scoping. The record schema, the coded records and the manuscript tables arrive notebook by notebook.

## Layout

```
notebooks/   numbered from 00; each ends with the standard commit cell
src/         paths, corpus handling, record schema and validation, grading, analysis, figures, tables
tools/       commit_cell.py, the single commit step
schema/      record schema, coding rules, search strings, outcome codes, card template
reports/     search log, screening, coded records (reports/records/), derived CSVs, findings, decisions
figures/     600 dpi figures with paper names in legends and axes
tables/      Word tables for the manuscript, each cell carrying its result id
tests/       checks that run without the network
data/        PDFs and downloads; ignored by git, never redistributed
```

## Working rules

- A record enters the tables only when its report was read in full; every paper-sourced field carries a page.
- Notebooks run on CPU and make no model calls.
- Commits go through `tools/commit_cell.py` from a notebook's last cell; it strips outputs, refuses `data/` and secrets, commits and pushes.

## Session bootstrap (first cell of every notebook)

```python
from google.colab import drive; drive.mount("/content/drive")
import os, sys, subprocess
PROJECT_ROOT = "/content/drive/MyDrive/SourceMap_Research"
REPO_DIR = PROJECT_ROOT + "/sourcemap-research"
os.environ["SOURCEMAP_PROJECT_ROOT"] = PROJECT_ROOT
os.environ["SOURCEMAP_REPO_ROOT"] = REPO_DIR
os.chdir(REPO_DIR); sys.path.insert(0, "src")
print(subprocess.run(["git", "pull", "--ff-only"], capture_output=True, text=True).stdout)
```

## Licence and citation

MIT licence. Citation details are in `CITATION.cff`.
