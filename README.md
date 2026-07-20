# ORION Cognitive Agent

Repositorio del **agente cognitivo** del proyecto ORION (Sistema Cognitivo
multi-repo). Construido con [LangChain Deep Agents](https://github.com/langchain-ai/deepagents)
sobre **AWS Bedrock** (Claude Sonnet) y desplegable en **Bedrock AgentCore
Runtime** (serverless managed) cuando se quiera correr en AWS.

## Descripción

Este repo contiene el **módulo de razonamiento cognitivo** de ORION: un
agente Python con memoria, herramientas (tools) y razonamiento multi-paso
expuesto vía API HTTP (FastAPI) compatible con el protocolo **AG-UI**
(consistente con el patrón de `spark-match-08-deep-agent`).

El agente se diseñó para tareas cognitivas genéricas (consulta,
planificación, recuperación de contexto). Su dominio funcional específico
se documenta en `docs/architectural-decisions/0001-stack.md`.

## Estado

| Componente | Estado | Notas |
|---|---|---|
| Stack & arquitectura | ✅ Definido | DeepAgents + langchain-aws + Bedrock |
| Bootstrap código | ✅ Mínimo | Agente placeholder operativo |
| Tests | ✅ Smoke test verde | Pytest configurado |
| Lint / Typecheck | ✅ Configurados | ruff + mypy strict |
| CI reusable | ✅ Cauce reusable | `spark-match-01-devops@main` |
| Despliegue `dev` | 🔜 Pendiente | Sprint siguiente |
| Producción `prod` | ❌ Fuera de scope | Solo `dev` por ahora |

## Repos del monorepo ORION

| Repo | Rol | Stack |
|---|---|---|
| `orion-frontend` | UI SPA | Angular 22 + Tailwind 4 |
| `orion-backend` | API transaccional | Node 24 + Lambda + TypeScript |
| **`orion-cognitive-agent`** | **Agente cognitivo (este repo)** | **Python + DeepAgents + Bedrock** |
| `orion-article` | Documentación académica | Markdown + LaTeX |
| `orion-infrastructure` | IaC AWS compartido | Terraform 1.x |

## Stack técnico

| Componente | Tecnología |
|---|---|
| Idioma | Python 3.12 (`.python-version`) |
| Framework del agente | `deepagents 0.6.x` (LangGraph runtime) |
| LLM | Amazon Bedrock (Claude Sonnet 4) via `langchain-aws` |
| API | FastAPI + SSE (AG-UI protocol, opcional) |
| Settings | Pydantic Settings 2.x (`ORION_AGENT_*`) |
| Linter | Ruff (format + check) |
| Type checker | mypy strict |
| Tests | Pytest + pytest-asyncio |
| Package manager | uv |

Ver detalle extendido y justificación de cada decisión en
`docs/architectural-decisions/`.

## Quickstart (entorno `dev`)

```bash
# 1. Clonar e instalar dependencias
git clone git@github.com:ahincho/orion-cognitive-agent.git
cd orion-cognitive-agent
uv sync --all-extras

# 2. Configurar variables de entorno
cp .env.example .env
# Editar .env con credenciales AWS (cuenta 681526276858, region us-east-1)
# y ORION_AGENT_MODEL_ID si quieres usar otro modelo distinto al default.

# 3. Ejecutar el agente en modo local (sin AWS Bedrock: opcional mock)
make run-local

# 4. O contra Bedrock (requiere `aws configure` o IAM role asumible):
ORION_AGENT_ENVIRONMENT=bedrock make run-local
```

El servidor arranca en `http://localhost:8000` (ver `Makefile` para los
demás targets).

## Estructura del proyecto

```
orion-cognitive-agent/
├── src/
│   └── orion_cognitive_agent/
│       ├── __init__.py        # API pública
│       ├── __main__.py        # Entry point: python -m orion_cognitive_agent
│       ├── config/            # Pydantic settings (env: local | bedrock | agentcore)
│       ├── agent/             # DeepAgent factory + (futuros subagentes)
│       ├── api/               # FastAPI app + servidor uvicorn
│       └── tools/             # @tool-decorated functions
├── tests/
│   └── test_smoke.py          # Smoke test: importa módulo + get_settings()
├── docs/
│   └── architectural-decisions/
│       ├── 0001-stack.md
│       ├── 0002-aws-target-bedrock-agentcore.md
│       └── 0003-monorepo-coordination.md
├── .env.example               # Plantilla de variables de entorno
├── .gitignore
├── .gitattributes
├── .dockerignore              # Imagen runtime AgentCore (futuro Sprint)
├── .python-version            # 3.12
├── .yamllint.yml
├── AGENTS.md                  # Convenciones operacionales (lectura obligatoria)
├── LICENSE                    # MIT (2026 ahincho)
├── Makefile                   # Targets: install, qa, test, run-local, clean...
├── pyproject.toml             # Deps + tooling (hatchling + ruff + mypy + pytest)
└── README.md                  # Este archivo
```

## Branching y contribución

Single-tier branching: `main` es la única rama permanente. Todo cambio va
en una rama `feat/<scope>`, `fix/<scope>`, `chore/<scope>`, etc. y entra
a `main` via PR con squash-merge. Las reglas detalladas (lifecycle,
Conventional Commits, forbidden operations) viven en `AGENTS.md`.

> **¿Por qué single-main y no main+dev?**  Es un repo solo-dev
> (<code>@ahincho</code>) sin colaboradores externos hoy. La rama <code>dev</code>
> agrega fricción sin entregar valor de "integración pre-prod" mientras
> no haya más de una persona trabajando en paralelo. Si en el futuro se
> suman colaboradores se migrará a main+dev con un PR explícito.

## Licencia

MIT — Copyright (c) 2026 ahincho. Ver [`LICENSE`](./LICENSE).
