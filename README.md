# Script-kiddie

![Script-kiddie logo](assets/logo.png)

Script-kiddie is an open-source **AI governance, testing, guardrails, and security assessment** platform for Vibe Coders and Vibe Engineers building LLM apps, agent frameworks, MCP servers, and non-human identities (NHIs).

It combines **static regex-based rules** (OWASP LLM Top 10, agent guardrails, data exfiltration, etc.), **AI-powered multi-judge review** (local Ollama models that confirm or reject findings), and **policy-as-code gating** (block / manual_review / allow decisions).

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 15 + React 19 + Tailwind CSS |
| Backend API | FastAPI + Uvicorn |
| Task Queue | Celery + Redis |
| Database | PostgreSQL 16 |
| LLM Integration | Ollama (local/private models) |
| Infrastructure | Docker Compose |

---

## Project Structure

```
Script-kiddie/
├── apps/
│   ├── api/                    # FastAPI backend + Celery worker
│   └── web/                    # Next.js UI
├── packages/
│   ├── core/                   # Rules scanner + SARIF formatter
│   ├── cli/                    # Command-line tool
│   └── model_gateway/          # LLM provider abstraction + judge orchestration
├── rulesets/                   # YAML rule definitions (10 rulesets)
├── policies/                   # YAML policy-as-code configs
├── snippets/                   # Secure code patterns library
├── infra/                      # Docker Compose configuration
└── .github/workflows/          # GitHub Actions (self-scan SARIF upload)
```

---

## Quickstart (Docker)

### 1. Start the Stack

```bash
cd infra
POSTGRES_PASSWORD=scriptkiddie REDIS_PASSWORD=scriptkiddie docker compose up -d --build
```

This launches 6 services: **PostgreSQL**, **Redis**, **Ollama**, **FastAPI**, **Celery worker**, and **Next.js**.

### 2. Pull an Ollama Model (first time only)

```bash
docker exec -it scriptkiddie-ollama ollama pull llama3.1
```

### 3. Open the UI

- **Web UI**: http://localhost:3000
- **API Health**: http://localhost:8000/health
- **API Docs**: http://localhost:8000/docs

---

## Scanning Your Own Code

The scanner runs inside Docker, so your code must be accessible to the containers. There are two ways to do this:

### Option A — Mount Your Code (Recommended)

Edit `infra/docker-compose.yml` and add a volume mount to both the `api` and `worker` services:

```yaml
# In the api and worker services, under volumes:
volumes:
  - /path/to/your/existing/code:/workspace/my-project:ro
```

Then restart the stack:

```bash
cd infra
docker compose down
POSTGRES_PASSWORD=scriptkiddie REDIS_PASSWORD=scriptkiddie docker compose up -d --build
```

### Option B — Copy Code Into Containers

```bash
docker cp /path/to/your/existing/code scriptkiddie-api:/workspace/my-project
docker cp /path/to/your/existing/code scriptkiddie-worker:/workspace/my-project
```

> Note: Copied files don't persist across container restarts.

### Run a Scan From the UI

1. Open **http://localhost:3000**
2. In **Target Path**, enter `/workspace/my-project` (matching where you mounted/copied your code)
3. Select a **ruleset** (e.g., `owasp-llm-top10.yml`)
4. Toggle **AI Review** on if you want the Ollama judges to analyze findings
5. Click **Run scan**
6. Click the **Job ID** link to view results

### Re-scan After Code Changes

If you mounted code via Option A, changes are reflected immediately. If you used Option B or changed code baked into the image, rebuild:

```bash
cd infra
POSTGRES_PASSWORD=scriptkiddie REDIS_PASSWORD=scriptkiddie docker compose build api worker
POSTGRES_PASSWORD=scriptkiddie REDIS_PASSWORD=scriptkiddie docker compose up -d api worker
```

---

## How It Works

### The Scanning Pipeline

When a scan job is submitted, the Celery worker executes a three-phase pipeline:

**Phase 1 — Static Rules Scan**
- Loads YAML ruleset definitions
- For each rule: matches file globs, applies keyword fast-path filters, runs regex patterns
- Records findings with line numbers, code snippets, and SHA256 fingerprints

**Phase 2 — AI Review (Multi-Judge)**
- Summarizes the first 25 readable files from the target
- **Analyzer model** reviews for: model output execution, tool abuse, secrets, unsafe persistence
- **Two judge instances** independently evaluate findings and return JSON verdicts with confidence scores
- Verdicts are aggregated with consensus logic and diversity bonuses

**Phase 3 — Policy Evaluation**
- Applies rule overrides and suppressions
- **Static gate**: If worst severity >= configured threshold (default: critical) -> BLOCK
- **Judge gate**: Uses aggregated judge decision with confidence thresholds
- **Final decision**: `block`, `manual_review`, or `allow`

---

## UI Pages

| Page | URL | What It Does |
|------|-----|-------------|
| **Dashboard** | `/` | Create new scan jobs |
| **Jobs** | `/jobs` | List all jobs with live status polling |
| **Job Detail** | `/jobs/[id]` | View findings, AI verdicts, download SARIF |
| **Analytics** | `/analytics` | Aggregate stats, severity/decision breakdowns, top rules |
| **Snippets** | `/snippets` | Browse secure code pattern library |

### Job Detail Page Shows:

- **Status**: queued -> running -> done
- **Decision**: block / manual_review / allow
- **Findings**: Rule ID, severity badge, file path, line number, code snippet, remediation advice
- **Model Calls**: Analyzer and judge calls with parsed verdicts, confidence scores, token usage
- **Download SARIF**: Export for GitHub Code Scanning or other SARIF-compatible tools

---

## Available Rulesets

| Ruleset | What It Checks |
|---------|---------------|
| `owasp-llm-top10.yml` | Model output in exec, hardcoded secrets, undefined tool permissions |
| `agent-guardrails.yml` | Prompt injection, model output in HTTP requests, long-lived credentials |
| `data-exfiltration.yml` | Data to external URLs, PII logging, unredacted context forwarding |
| `agentic-tool-abuse.yml` | Agent tool abuse patterns |
| `model-supply-chain.yml` | Model supply chain risks |
| `rag-poisoning.yml` | RAG poisoning vectors |
| `multi-tenant-isolation.yml` | Tenant isolation issues |
| `nhi-lifecycle.yml` | Non-human identity lifecycle |
| `mcp-hardening.yml` | MCP server hardening |

### Rule Format

```yaml
rules:
  - id: SK-XXX-001
    title: "Rule name"
    severity: critical|high|medium|low
    category: llm-security|agent-security|data-security|nhi-security
    file_globs: ["**/*.py", "**/*.js"]
    exclude_globs: ["**/test_*.py"]
    keywords: ["keyword1", "keyword2"]   # Fast-path filter
    patterns: ["regex1", "regex2"]        # Compiled with IGNORECASE
    message: "Issue description"
    remediation: "How to fix it"
    cwe_ids: ["CWE-78"]
    owasp_ids: ["LLM02"]
```

---

## Policy-as-Code

Default policy (`policies/default.yml`):

```yaml
policy:
  id: default
  title: Default policy
  block_if_severity_at_or_above: critical
  judge_block_confidence_threshold: 0.75
  judge_allow_confidence_threshold: 0.75
  require_consensus_to_allow: false
  decisions: [block, manual_review, allow]
  rule_overrides: []
```

---

## API Endpoints

**Base URL**: `http://localhost:8000` (write endpoints require `X-API-Key` header)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/jobs` | Create scan job |
| `GET` | `/jobs` | List all jobs |
| `GET` | `/jobs/{id}` | Job details |
| `GET` | `/jobs/{id}/results` | Job findings + model calls |
| `GET` | `/jobs/{id}/sarif` | Export SARIF |
| `GET` | `/jobs/{id}/export?format=json\|csv\|md` | Export findings |
| `GET` | `/jobs/{id}/diff?baseline_job_id=X` | Diff two scans |
| `POST` | `/findings/{fingerprint}/suppress` | Suppress a finding |
| `DELETE` | `/findings/{fingerprint}/suppress` | Unsuppress a finding |
| `GET` | `/suppressions` | List suppressions |
| `GET` | `/snippets` | List snippets |
| `GET` | `/stats` | Aggregate statistics |
| `POST` | `/webhooks` | Register webhook |

---

## API Authentication

Simple API key model for the MVP:

- Set `API_KEY` in `apps/api/.env` (default: `dev-local-key`)
- Pass as header: `X-API-Key: dev-local-key`
- The Web UI uses `NEXT_PUBLIC_API_KEY` to call the API
- Comparison uses `hmac.compare_digest()` (timing-safe)

---

## CLI Usage

Install locally:

```bash
python -m pip install -e packages/core -e packages/cli
```

Run a scan:

```bash
scriptkiddie scan --root /path/to/code --ruleset rulesets/owasp-llm-top10.yml --format sarif --out results.sarif
```

Other commands:

```bash
scriptkiddie rules list --repo-root .
scriptkiddie diff --current current.sarif --baseline baseline.sarif
scriptkiddie validate-ruleset rulesets/owasp-llm-top10.yml
scriptkiddie validate-policy policies/default.yml
```

---

## GitHub Code Scanning Integration

This repo includes a GitHub Actions workflow that runs Script-kiddie rules and uploads SARIF to GitHub Code Scanning. Findings appear as PR annotations.

See `.github/workflows/code-scanning-sarif.yml`.

Triggers on: push to main, PR to main, weekly schedule (Monday).

---

## Testing

```bash
# Run all tests in Docker (recommended)
make test-docker

# Or locally
pytest -q packages/core/tests packages/model_gateway/tests packages/cli/tests apps/api/tests
```

---

## Environment Configuration

Copy the example env file and customize:

```bash
cp apps/api/.env.example apps/api/.env
```

Key variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | — | PostgreSQL connection string |
| `REDIS_URL` | — | Redis broker URL |
| `API_KEY` | `dev-local-key` | API authentication key |
| `OLLAMA_BASE_URL` | `http://ollama:11434` | Ollama server URL |
| `OLLAMA_MODEL_ANALYZER` | `llama3.1` | Model for code analysis |
| `OLLAMA_MODEL_JUDGE` | `llama3.1` | Model for judge verdicts |
| `POLICY_PATH` | `policies/default.yml` | Default policy file |
| `CORS_ORIGINS` | `http://localhost:3000` | Allowed CORS origins |

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
