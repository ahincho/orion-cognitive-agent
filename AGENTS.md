# AGENTS.md

> Convenciones operacionales para el repo `orion-cognitive-agent`. Lectura
> **obligatoria** antes de cada PR. Fuente de verdad local (no duplicada en
> `docs/`).

---

## Proyecto

**ORION - Sistema Cognitivo**. Repositorio parte de un monorepo de **5**
repositorios coordinados:

| Repo | Rol |
|---|---|
| [`orion-frontend`](https://github.com/ahincho/orion-frontend) | UI SPA (Angular 22) |
| [`orion-backend`](https://github.com/ahincho/orion-backend) | API transaccional (Lambda + TS) |
| **`orion-cognitive-agent`** | **Este repo — agente cognitivo (Python + Bedrock)** |
| [`orion-article`](https://github.com/ahincho/orion-article) | Documentación académica |
| [`orion-infrastructure`](https://github.com/ahincho/orion-infrastructure) | IaC AWS compartido |

Este repo contiene el **agente cognitivo** del sistema: razonamiento
multi-paso, memoria, tools, expuesto vía HTTP/AG-UI. La integración con
el resto del monorepo se documenta en
[`docs/architectural-decisions/0003-monorepo-coordination.md`](docs/architectural-decisions/0003-monorepo-coordination.md).

## Stack

- **Cloud:** AWS (cuenta `681526276858`, region `us-east-1`) — único ambiente
  es `dev` (ver "Single environment" abajo).
- **Idioma:** Python `>= 3.12` (pin exacto en `.python-version`).
- **Package manager:** [`uv`](https://docs.astral.sh/uv/) — lock file
  versionado (`uv.lock`), build via `hatchling`.
- **Framework del agente:** [`deepagents`](https://github.com/langchain-ai/deepagents)
  `>= 0.6.12` (LangGraph runtime) sobre
  [`langchain-aws`](https://github.com/langchain-ai/langchain-aws) `>= 1.6.1`.
- **LLM:** Amazon Bedrock (Claude Sonnet 4 por defecto) via
  `ChatBedrockConverse`.
- **API:** FastAPI + SSE (compatible con AG-UI opcional).
- **Settings:** Pydantic Settings 2.x con namespace `ORION_AGENT_*`.
- **Lint/format:** Ruff (`ruff check` + `ruff format`).
- **Type check:** mypy strict (`disallow_untyped_defs`, `no_implicit_optional`,
  `warn_unused_ignores`, etc.).
- **Tests:** Pytest + pytest-asyncio (`asyncio_mode = "auto"`).
- **CI:** workflows reutilizables desde
  [`spark-match/spark-match-01-devops@main`](https://github.com/spark-match/spark-match-01-devops)
  (actionlint, gitleaks, yamllint) + workflow propio para `test`/`lint`/`typecheck`.

Pin de reusables: **siempre `@main`**. Los reusables de
`spark-match-01-devops` fueron promovidos de `@dev` (PR #45) tras un
periodo de bake-time; no volver a `@dev` salvo decisión explícita.

### Single environment (dev)

> **Solo `dev`. No hay staging ni prod.**

Razón: este agente aún no tiene usuarios finales; corre exclusivamente
para el dueño del proyecto (`@ahincho`) en local o en AWS `dev`. Si en
el futuro se quisiera exponer públicamente, se reabre la conversación
arquitectónica — no se promueve automáticamente.

Variables de entorno clave (todas con prefijo `ORION_AGENT_*`):
- `ORION_AGENT_ENVIRONMENT` ∈ {`local`, `bedrock`, `agentcore`}
  (default: `local`; el valor `agentcore` activa paths para Bedrock
  AgentCore Runtime — Sprint futuro).
- `ORION_AGENT_MODEL_PROVIDER` ∈ {`bedrock`} (extensible a `openai` /
  `anthropic` / `ollama` en runtime futuro).
- `ORION_AGENT_MODEL_ID` (default: `us.anthropic.claude-sonnet-4-20250514`).
- `ORION_AGENT_AWS_REGION` (default: `us-east-1`).

### Secrets

- **En local (dev)**: `.env` (ignorado) cargado por Pydantic Settings.
- **En CI**: secrets de GitHub Actions (`ORION_AGENT_*` equivalentes).
- **En AWS**: IAM role asumido por GitHub OIDC (`orion-agent-dev`)
  provisionado por `orion-infrastructure` (Sprint de IaC futuro).

**Nunca** commitear credenciales, keys ni valores de `ORION_AGENT_*` —
el `.gitignore` lo blinda y `gitleaks` en CI lo audita.

## Git Workflow (mandatory)

Single-tier branching (rapid solo project). Validar siempre que la
cuenta activa sea `ahincho`:

```bash
gh api user --jq .login
# o
ssh -T git@github.com
```

- `main` es la única rama permanente. PRs van contra `main` directamente.
- Todo trabajo ocurre en una rama `feat/<scope>`, `fix/<scope>`,
  `chore/<scope>`, `docs/<scope>`, `ci/<scope>`, etc.
- **No** hay rama `dev` de integración (ver "Single environment").

### Lifecycle de cada cambio

1. `git fetch origin && git checkout main && git pull --ff-only origin main`.
2. `git checkout -b <type>/<scope>` desde `main`.
3. Implementar, commitear con **Conventional Commits** + scope (`feat(auth): ...`,
   `chore(ci): ...`).
4. Validar localmente: `make qa` + `make test`.
5. `git push -u origin <type>/<scope>`.
6. Abrir PR **desde `<type>/<scope>` a `main`**.
7. Tras CI verde, **squash-merge a `main`**.
8. Branch borrada automáticamente por el ruleset.

### Forbidden

- Commit directo a `main` (forzado por ruleset).
- Force-push a `main` (forzado por ruleset `non_fast_forward`).
- Merge commits en `main` (squash-only habilitado en repo settings).
- Auto-merge en PRs (deshabilitado a nivel repo).

> El autor no puede aprobar su propio PR (regla de GitHub). Para PRs
> propios, squash-merge con `--admin` queda como escape-hatch documentado
> en `docs/architectural-decisions/0004-self-approval.md` (TODO Sprint).

## Convenciones de código (Python)

- Routing/nombres/identificadores en **English**; docstrings/comments en
  **English** (consistencia con `spark-match-08-deep-agent`).
- Type hints obligatorios. Toda función pública con signature anotada.
- No `Any` ni `cast` salvo justificación en línea.
- Imports ordenados por ruff (`I`).
- `__init__.py` exporta la API pública con `__all__`.
- Tests bajo `tests/<dominio>/<módulo>.py` (convención del reference;
  pytest los recoge por configuración, no por prefijo `test_`).
- Commits: Conventional Commits + scope (`feat(agent): ...`).
- Tags: `git tag -a vX.Y.Z -m "release vX.Y.Z"` (semver), todavía no
  automatizado en este repo.

## Antes de la primera iteración real

Este repo está en **bootstrap**. El código que se agregue debe seguir
los patrones de `src/orion_cognitive_agent/` ya establecidos. Cada
cambio sigue el stack declarado arriba y se integra con el resto del
monorepo vía el repo `orion-infrastructure` (cuando aplique IaC AWS).

## Contacto

- Owner: `@ahincho` (solo-dev). PR reviews propios requieren `--admin`
  hasta que se sume un colaborador.
- Repo hermano de referencia: [`spark-match-08-deep-agent`](https://github.com/spark-match/spark-match-08-deep-agent)
  — mismo stack, mismo Makefile, mismo formato de Pydantic Settings. Si
  dudas sobre estructura, alineate con él.
