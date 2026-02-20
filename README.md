# Script-kiddie
![Script-kiddie logo](assets/logo.png)

Script-kiddie is an open-source platform for Vibe Coders and Vibe Engineers that assist in **AI governance, testing, guardrails, and security assessments**
for LLM apps, agent frameworks, MCP servers, and non-human identities.

This repo is an **MVP platform** that ships:
- **Web UI**: Next.js + Tailwind
- **API**: FastAPI
- **Worker**: Celery + Redis
- **DB**: Postgres (jobs, findings, model calls, audit events)
- **Rules scan**: YAML rulesets + regex/keyword checks
- **Ollama multi-judge**: multiple local/private model passes to validate/critique findings
- **Policy-as-code**: YAML policies (block/allow thresholds)
- **SARIF export**: to integrate with GitHub code scanning / PR gates
- **Snippets library**: secure copy/paste patterns

---

## Quickstart (Docker)

### 1) Start everything
```bash
cd infra
POSTGRES_PASSWORD=scriptkiddie REDIS_PASSWORD=scriptkiddie docker compose up -d --build
```

### 2) Pull an Ollama model (first time)
In another terminal:
```bash
docker exec -it scriptkiddie-ollama ollama pull llama3.1
```

### 3) Open the UI
- Web: http://localhost:3000
- API: http://localhost:8000/health

### 4) Run a test scan from the UI
1. Open `http://localhost:3000`.
2. In **Create a scan job**, keep **Target path** as `/workspace` (or enter another allowed in-container path).
3. Click **Run scan**.
4. Click **View job →**.
5. On the job page, watch:
   - **Status** (queued → running → done)
   - **Decision** (allow / block / manual_review)
   - **Findings**
   - **Model calls** (analyzer + judges)
6. Click **Download SARIF** to export scan output for CI/code-scanning tools.

### 5) Re-scan after code changes
If you change source code locally, rebuild the API/worker images so `/workspace` in the containers has the latest code:

```bash
cd infra
POSTGRES_PASSWORD=scriptkiddie REDIS_PASSWORD=scriptkiddie docker compose build api worker
POSTGRES_PASSWORD=scriptkiddie REDIS_PASSWORD=scriptkiddie docker compose up -d api worker
```

---

## Basic workflow

1) Create a scan job in the UI (default target path: `/workspace`)
2) The worker runs:
   - Rules-based scan
   - Ollama judges validate findings (self-consistency)
   - Policy evaluation decides: allow / block / manual_review
3) View findings + judges in the Job detail page
4) Export SARIF from the Job detail page (or API)

---

## API Auth (simple MVP)
API uses an API key for write endpoints.

Set `API_KEY` in `apps/api/.env` (default is `dev-local-key`).
Pass it as header:

`X-API-Key: dev-local-key`

The Web UI calls the API with the same key via `NEXT_PUBLIC_API_KEY`.

---

## Key folders
- `apps/api` – FastAPI + Celery worker
- `apps/web` – Next.js UI
- `packages/core` – rules scanner + SARIF formatter
- `packages/model_gateway` – Ollama provider + multi-judge orchestration
- `rulesets/` – YAML rule packs
- `policies/` – YAML policy-as-code
- `snippets/` – secure copy/paste patterns
- `infra/` – docker-compose

---

## Contributing
See **CONTRIBUTING.md**. Great first PRs:
- Add rulesets (agent tool allowlists, memory isolation, MCP config hardening)
- Improve judge parsing + aggregation
- Add more snippets (structured output, tool gating, redaction)
- Add more languages to rules/snippets (TS, Go, Java)

---

## License
Apache-2.0


## GitHub Code Scanning (SARIF)
This repo includes a workflow that runs Script-kiddie rules and uploads SARIF to GitHub Code Scanning.
See `.github/workflows/code-scanning-sarif.yml`.
## CLI

Install for local dev:
```bash
python -m pip install -e packages/core -e packages/cli
```

Run a scan:
```bash
scriptkiddie scan --root . --ruleset rulesets/owasp-llm-top10.yml --out script-kiddie.sarif --format sarif
```

List rulesets:
```bash
scriptkiddie rules list --repo-root .
```
