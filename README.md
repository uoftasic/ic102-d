# IC102-D — Working in Tiny Tapeout Repos (Digital)

Make a digital Tiny Tapeout project from the template on your own GitHub account and keep its workflows passing.

The course site, with the reading and the lab writeups, is published at
<https://uoftasic.com/ic102-d/>. Students get this repository in the workbench from IC101 with
`mod add ic102-d`, and start at [Lab 01](docs/labs/lab-01-your-repo-from-the-template-overview.md).
IC102-A, the analog version, lives in [uoftasic/ic102-a](https://github.com/uoftasic/ic102-a); the
eight guide pages the two versions share are written here and copied there by
`scripts/sync_shared_pages.py`.

Org: [github.com/uoftasic](https://github.com/uoftasic)

## What's here

| Path | What it is |
|---|---|
| `docs/` | The Quarto site: the home page with the course path, `guide/` for reading, `labs/` for the lab writeups |
| `labs/common/tt-tools/` | The tools of Tiny Tapeout's `test` and `gl_test` jobs at the runner's versions, installed next to the workbench's, and `make test` |
| `labs/common/ic102.py`, `check-runs.py` | The git and GitHub helpers the lab checkers share; `check-runs.py` prints every job's result on a commit |
| `labs/lab-01-your-repo-from-the-template/` | Lab 01's checker |
| `labs/lab-02-read-the-red-x/` | The breakage script, the `DIAGNOSIS.md` template and the checker |
| `labs/lab-03-make-it-yours/` | The counter, its starter test, the planted bug and the checker |
| `labs/lab-04-a-change-through-review/` | The review sandbox each student copies into a repository of their own (`sandbox/`), `claim.py`, `check-pr.py`, and the AI-written pull request for Part 6 (`ai-pr.py`) |
| `labs/lab-05-find-the-commit-that-broke-it/` | The prepared history as a git bundle, its builder, the bisect template and the checker |

## Building the site

```bash
quarto preview docs
# → http://localhost:4200
quarto render docs --profile pdf --to typst
# → the whole course as one PDF in docs/_book/
```

## Layout

| Path | On Pages? | Purpose |
|------|-----------|---------|
| `docs/` | Yes | The Quarto site students read (`docs/_quarto.yml`) |
| `docs/guide/` | Yes | Guide pages: reading only |
| `docs/labs/` | Yes | Lab writeups: the steps students follow |
| `labs/` | No | Runnable packages (HDL, Python, data, graders) |
| `scripts/` | No | Team utilities and automation |
| `notebooks/` | No | Exploratory and assignment notebooks |
| `data/`, `figures/` | No | Shared datasets and source figures |

## GitHub Pages

| Setting | Value |
|---------|--------|
| Source | GitHub Actions |

`.github/workflows/site.yml` renders `docs/` with Quarto whenever a push to `main` changes `docs/`, `scripts/check_site.py` or the workflow itself, and deploys `docs/_site`, which includes a PDF of every page and the whole-course PDF.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE). Copyright UofT ASIC Team / `uoftasic`.
