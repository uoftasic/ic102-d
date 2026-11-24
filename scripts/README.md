# Scripts

Utilities for IC102-D — Working in Tiny Tapeout Repos (Digital) under the UofT ASIC org (`uoftasic`).

## Entry points

| Script | Purpose |
|--------|---------|
| `check_site.py` | Check that every local link and `#anchor` in the rendered site resolves, and that every page has the navbar's link to https://edu.uoftasic.com/; `.github/workflows/site.yml` runs it on `docs/_site` |
| `init-template.py` | Fill `ic102-d` / title / description after using the template |
| `sync_shared_pages.py` | Copy the eight guide pages IC102-D and IC102-A share, with their images and figure scripts, into the other course repo and report what differs: `python3 scripts/sync_shared_pages.py ../ic102-a --dry-run`, then without `--dry-run` to copy. The shared pages are edited here, in ic102-d, and only copied into ic102-a |
| `figures/` | The scripts that draw the diagrams in `docs/assets/img/` with schemdraw. `pip install -r scripts/figures/requirements.txt`, then `python3 scripts/figures/<name>.py` rewrites that figure's SVG |

## Usage

```bash
# From repo root

python3 scripts/init-template.py \
  --id dd103 \
  --title "DD103 — RTL on FPGAs & ASICs" \
  --description "RTL on FPGAs and open-source ASIC flows"
```

## Conventions

- Write scripts in Python where you can. HDL tooling belongs in `labs/` or the shared workbench.
- Keep secrets out of the repo. If a script needs configuration, add a `.env.example`.
- When you add a script, add it to the table above.
