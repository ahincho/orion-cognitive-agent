# Architectural Decision Records

Este directorio contiene las decisiones arquitectónicas irreversibles (o
cuyo costo de reversión es alto) que han guiado el diseño de
`orion-cognitive-agent`.

Cada decisión se documenta en un archivo `NNNN-titulo-corto.md` siguiendo
el formato simplificado de Michael Nygard.

| ADR | Título | Estado | Fecha |
|---|---|---|---|
| [0001](./0001-stack.md) | Stack del agente (DeepAgents + langchain-aws + Bedrock) | Accepted | 2026-07-20 |
| [0002](./0002-aws-target-bedrock-agentcore.md) | AWS hosting target (Bedrock AgentCore Runtime) | Proposed | 2026-07-20 |
| [0003](./0003-monorepo-coordination.md) | Coordinación con el monorepo ORION | Accepted | 2026-07-20 |

## Plantilla para nuevas ADRs

```markdown
# ADR-NNNN — <título>

| Campo | Valor |
|---|---|
| Estado | Proposed | Accepted | Deprecated | Superseded by NNNN |
| Fecha | YYYY-MM-DD |
| Decisión | <frase en una línea> |

## Contexto
<problema y alternativas consideradas>

## Decisión
<qué decidimos>

## Consecuencias
**Positivas:** …
**Negativas / riesgos:** …

## Próximos pasos (si aplica)
- [ ] …

## Revisores
- @user
```
