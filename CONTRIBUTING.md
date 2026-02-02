# Contributing

## Local dev (recommended)
```bash
cd infra
docker compose up --build
```

## Adding a rule
Rules are YAML in `rulesets/`. Keep them:
- language/file-targeted (`file_globs`)
- low false-positive
- with a clear remediation

## Adding a snippet
Add a folder under `snippets/<lang>/<name>/` with:
- `snippet.md`
- `meta.json` (title, tags, description, language)

## Pull request checklist
- No secrets
- Tests / minimal validation where possible
- UI changes include screenshots
## Pre-commit (recommended)
Install once:
```bash
python -m pip install -U pre-commit
pre-commit install
```

Run on all files:
```bash
pre-commit run --all-files
```
