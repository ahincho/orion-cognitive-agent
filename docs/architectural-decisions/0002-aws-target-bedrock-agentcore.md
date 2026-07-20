# ADR-0002 — AWS hosting target (Bedrock AgentCore Runtime)

| Campo | Valor |
|---|---|
| Estado | **Proposed** (implementación diferida a Sprint futuro) |
| Fecha | 2026-07-20 |
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
- [ ] Workflow `deploy-dev.yml`: build imagen, push a ECR, deploy a
  AgentCore Runtime.
- [ ] Pydantic `ORION_AGENT_ENVIRONMENT=agentcore` paths completos en
  `agent/factory.py`.
- [ ] Documentación operativa de despliegue en `docs/deployment.md`.

## Revisores

- `@ahincho`.
