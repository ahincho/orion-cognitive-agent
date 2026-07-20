# ADR-0002 — AWS hosting target (Bedrock AgentCore Runtime)

| Campo | Valor |
|---|---|
| Estado | **Partially Accepted** (factory + middleware + tools en Sprint A; deploy a AgentCore sigue diferido) |
| Fecha | 2026-07-20 (creación), 2026-07-20 (Sprint A update) |
| Decisión | El agente se desplegará en **Bedrock AgentCore Runtime** cuando se salga de local |

## Contexto

Hoy el agente corre localmente (`uv run uvicorn ...`). Cuando llegue el
momento de exponerlo al `orion-frontend` y a `orion-backend`, hay que
elegir un AWS compute target. Las opciones evaluadas:

1. **Bedrock AgentCore Runtime** — servicio serverless managed de AWS,
   hecho específicamente para agentes Bedrock-native.
2. **AWS Lambda + `bedrock-runtime` SDK directo** — mismo patrón que
   `orion-backend` (Lambda por caso de uso).
3. **ECS Fargate / App Runner** con contenedor FastAPI propio — más
   control, más caro.

El agente es **cognitivo, de baja-media escala y altamente stateful**
(típicamente mantiene estado conversacional por minutos, con bursts de
5–20 tool calls por turno). El deployment serverless managed encaja
mejor que Lambda puro (latencia cold-start) o un contenedor dedicado
(costos fijos altos).

## Decisión

Adoptamos **Bedrock AgentCore Runtime** como destino de despliegue.
Esto se traducirá en:

- Imagen Docker del agente servida al runtime (build via workflow
  `deploy-dev.yml` aún no creado).
- IAM role asumido por GitHub OIDC: nombre tentativo
  `orion-agent-dev`, creado por módulo Terraform en `orion-infrastructure`
  (sprint siguiente).
- Activación de paths runtime de `ORION_AGENT_ENVIRONMENT=agentcore` en
  el factory del agente (ver `src/orion_cognitive_agent/agent/factory.py`).
- Configuración de `AgentCore Memory` para memoria cross-session
  (reemplazo del langmem/StateBackend actual).
- Observabilidad vía CloudWatch + X-Ray + OpenTelemetry (export a
  LangSmith opcional vía `ORION_AGENT_LANGSMITH_TRACING=true`).

Mientras tanto, **local** y **bedrock** siguen siendo los modos
operativos del bootstrap. El switch se activa con sólo
`ORION_AGENT_ENVIRONMENT=agentcore` (sin cambiar código).

## Estado de implementación (Sprint A)

| Pieza | Estado | Notas |
|---|---|---|
| `Environment` enum (`local` / `bedrock` / `agentcore`) | ✅ | `src/orion_cognitive_agent/config/settings.py` |
| `ORIONAgent` dataclass handle (frozen) | ✅ | `src/orion_cognitive_agent/agent/factory.py`. `graph: CompiledStateGraph \| None` para futuro deepagent compilado |
| `create_orion_agent(settings)` local (metadata-only) | ✅ | No hace llamadas AWS; útil para dev offline + tests |
| `create_orion_agent(settings)` bedrock (deepagent real) | ✅ | `create_deep_agent` con `model=settings.model_string` → langchain-aws resuelve `bedrock:*` a `ChatBedrockConverse` |
| `create_orion_agent(settings)` agentcore | ✅ (mismo path que bedrock; diferenciación en runtime se delega al container protocol, Sprint C) | El switch se activa por env var, sin código adicional |
| `MaxTurnsMiddleware` | ✅ | `src/orion_cognitive_agent/agent/middleware.py`. Patrón espejo del reference |
| `aws.get_bedrock_runtime_client()` lazy + cached | ✅ | `src/orion_cognitive_agent/aws/client.py`. Backdoor para tools que necesiten `bedrock-runtime` directo sin pasar por langchain-aws |
| `tools.echo` (handler + tool split) | ✅ | `src/orion_cognitive_agent/tools/echo/`. Andamiaje mínimo viable; se depreca cuando llegue la primera tool de dominio |
| `prompts.coordinator.md` (versioned) | ✅ | `src/orion_cognitive_agent/prompts/`. Cargado por `prompts.loader.load_prompt("coordinator")` |
| LangSmith wiring (`configure_langsmith`) | ✅ | `src/orion_cognitive_agent/observability/langsmith.py`. Idempotente, opt-in por env var |
| `Settings.model_string` property | ✅ | Devuelve `"bedrock:<model_id>"` para `create_deep_agent` |
| `api.app` con `lifespan` + CORS + logging setup | ✅ | Logging y LangSmith se configuran una sola vez por proceso (idempotente) |
| Tests: `TestAgentFactoryBedrock` (skip si no bedrock group) | ✅ | Valida graph compilation sin invocar Bedrock |
| `Settings.langsmith_*` + `Settings.agent_name` | ✅ | Model fields con secret masking para `langsmith_api_key` |

**Diferido a Sprint C / infra:**

- Imagen Docker del agente (`.dockerignore` ya está listo).
- IAM role `orion-agent-dev` provisionado por módulo Terraform en `orion-infrastructure`.
- Workflow `deploy-dev.yml` (build + ECR push + AgentCore deploy).
- Active session / budget tracker (análogo al `budget.py` del reference; no
  requerido para Sprint A porque solo hay una tool y no hay per-tool
  budgets que valga la pena guardar).
- `AgentCore Memory` para memoria cross-session (reemplazo del
  langmem/StateBackend eventual).
- Streaming real `/ag-ui` vía `ag-ui-langgraph` (hoy sigue como placeholder).

## Adaptación deepagents → AgentCore Runtime

El container de Bedrock AgentCore Runtime espera:

1. Una imagen Docker que exponga un HTTP server (puerto 8080 por
   convención; configurado via `PORT` env var pasado al container).
2. Un endpoint `/invocations` que recibe requests POST con el payload
   del protocolo AgentCore, y devuelve respuestas estructuradas.
3. Un endpoint `/ping` para health probes (el orchestrator hace
   liveness cada N segundos).

Mapping del factory:

- `Environment.LOCAL`     — corre el FastAPI actual (puerto 8000); útil
  para iterar en máquina del dev.
- `Environment.BEDROCK`   — corre el FastAPI actual apuntando a Bedrock
  vía credenciales del entorno; útil para validar prompts/tools sin
  pagar el costo del deploy.
- `Environment.AGENTCORE` — corre el FastAPI en el container con el
  `PORT=8080` y los endpoints `/invocations` + `/ping` que AgentCore
  espera (Sprint C). El deepagent graph es el mismo en los tres modos —
  solo cambia el transport.

## Consecuencias

**Positivas:**

- Costos proporcionales al uso (sin pagar por capacidad ociosa).
- Auto-scaling implícito; cero gestión del contenedor.
- Integración nativa con `Bedrock` (sin credenciales adicionales).
- Memoria cross-session gestionada por AgentCore Memory (vs
  responsabilidad del app).

**Negativas / riesgos:**

- **Vendor lock-in**: la imagen debe cumplir el contrato del runtime;
  migrar a otro compute target requiere rebuild.
- **Cold start** mayor que un Lambda dedicado (dependiente de tamaño
  de la imagen). Mitigable manteniendo la imagen ligera
  (`.dockerignore` ya cuida eso).
- **Dependencia de IaC**: el despliegue requiere el módulo Terraform en
  `orion-infrastructure` listo. Si esa pieza se atrasa, bloquea
  este repo.

## Sprint objetivo (TODO)

- [ ] Módulo Terraform `orion-infrastructure/modules/orion-agent-iam-dev/`
  con OIDC + IAM role.
- [ ] Módulo Terraform `orion-infrastructure/modules/ecr-orion-agent/`
  con repo ECR + policy de imagen inmutable.
- [ ] Module Terraform `orion-infrastructure/modules/bedrock-agentcore-runtime/`
  con la definición del Runtime + endpoint público.
- [ ] Workflow `.github/workflows/deploy-dev.yml` con steps
  `actions/checkout` → `aws-actions/configure-aws-credentials` (rol
  `orion-agent-dev`) → `make qa` (gate de calidad) → `docker build`
  → `aws ecr get-login-password` + `docker push` →
  `aws bedrock-agentcore update-agent-runtime` (idempotente).
- [ ] Documentación operativa de despliegue en `docs/deployment.md`.

## Revisores

- `@ahincho`.
