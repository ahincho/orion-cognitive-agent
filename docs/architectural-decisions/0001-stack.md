# ADR-0001 — Stack del agente (DeepAgents + langchain-aws + Bedrock)

| Campo | Valor |
|---|---|
| Estado | **Accepted** |
| Fecha | 2026-07-20 |
| Decisión | Stack del agente cognitivo sobre DeepAgents + langchain-aws + AWS Bedrock |

## Contexto

El módulo cognitivo de ORION debe construir un agente Python que combine
memoria, tools y razonamiento multi-paso. Las alternativas evaluadas son:

1. **DeepAgents + langchain-aws** (LangChain/LangGraph stack).
2. **Bedrock nativo** vía `boto3` + `bedrock-runtime`.
3. **Strands Agents SDK** (AWS-native, sin LangChain).

El equipo trae experiencia previa consolidada con el stack LangChain
(vía `spark-match-08-deep-agent`), incluyendo los patrones de sub-agentes,
tools y middleware. Adicionalmente, la ORION stack apunta a una
arquitectura donde:

- El frente (`orion-frontend` Angular) se conecta vía AG-UI (mismo
  protocolo que el DeepAgent de spark-match).
- El backend transaccional (`orion-backend`, Lambda + TS) consume al
  agente vía HTTP.
- Los tools del agente llaman a AWS (Bedrock, EventBridge) usando
  credenciales IAM.

## Decisión

Adoptamos **DeepAgents ≥ 0.6.12 + langchain-aws ≥ 1.6.1** como framework
del agente, con **Amazon Bedrock** como provider LLM (Claude Sonnet 4
por defecto).

- Idioma: **Python ≥ 3.12** (pin exacto en `.python-version`).
- Runtime hosting: se documenta por separado en
  [`0002-aws-target-bedrock-agentcore.md`](0002-aws-target-bedrock-agentcore.md).
- Package manager: **`uv`** (lock versionado).
- Config: **Pydantic Settings 2** con namespace `ORION_AGENT_*`.
- Lint/format: **Ruff**. Type-check: **mypy strict**. Tests: **Pytest**
  + `pytest-asyncio` (`asyncio_mode = "auto"`).

Las dependencias runtime opcionales (`deepagents`, `langchain-aws`)
viven en el dependency group `bedrock` (PEP 735) para que `uv sync` por
defecto produzca una imagen ligera sin AWS libs.

## Consecuencias

**Positivas:**

- Re-uso de patrones ya probados en `spark-match-08-deep-agent` (factory,
  middleware, prompts como `*.md`, AG-UI endpoint).
- Migración futura a AgentCore Runtime es solo cambio del path de
  inicialización — el agente sigue siendo el mismo objeto Python.
- Stack agnóstico al provider LLM: cambiar de Bedrock a OpenAI o
  Anthropic directo es cambio en `Settings.model_provider` +
  nueva rama en `agent/factory.py`.

**Negativas / riesgos:**

- Acoplamiento al ecosistema LangChain (release cadence rápido,
  breaking changes ocasionales — mitigado por `>=` ranges y `uv.lock`).
- Documentación interna debe distinguir patrones "deepagents-deprecated"
  vs "deepagents-0.6.x" para evitar referenciar docs viejas.

## Revisores

- `@ahincho` (autor y reviewer único por ahora).
