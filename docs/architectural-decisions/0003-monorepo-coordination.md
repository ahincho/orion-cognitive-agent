# ADR-0003 — Coordinación con el monorepo ORION

| Campo | Valor |
|---|---|
| Estado | **Accepted** |
| Fecha | 2026-07-20 |
| Decisión | Coordinación entre los 5 repos ORION vía contratos versionados y PRs cruzadas |

## Contexto

ORION es un monorepo distribuido en 5 repos de GitHub:

| Repo | Rol | Estado |
|---|---|---|
| `orion-frontend` | Angular SPA | Bootstrap |
| `orion-backend` | API Lambda + TS | Bootstrap |
| `orion-cognitive-agent` | Deep Agent (este repo) | Bootstrap |
| `orion-article` | Paper académico | Bootstrap |
| `orion-infrastructure` | IaC AWS | Bootstrap |

Aún no hay un "release train" formal: cada repo es independiente y los
despliegues se orquestarán desde `orion-infrastructure`. Pero a medida
que el sistema crezca necesitamos reglas claras para evitar drift
silencioso entre versiones.

## Decisión

Adoptamos el siguiente modelo de coordinación (mínimo viable hoy,
evolucionable):

1. **Contratos por tag semver**: cada repo declara la versión de los
   contratos que consume en su `pyproject.toml` (o `package.json`).
   Ejemplo: `orion-backend` declara la versión del esquema de eventos
   EventBridge que emite `orion-cognitive-agent`.
2. **Versionado de eventos / schemas JSON** en un repositorio futuro
   `orion-contracts` (Sprint siguiente). Mientras tanto, los schemas
   viven dentro de cada repo y se documentan en `docs/`.
3. **PRs cruzadas** cuando se cambia un contrato: `orion-cognitive-agent`
   publica un cambio de schema → PR en `orion-backend` que migra al
   nuevo formato con `bump-deps` apuntando al nuevo tag.
4. **CHANGELOG por repo** (semver estricto: MAJOR.MINOR.PATCH) → los
   consumidores pueden auditar el impacto antes de bumpear.
5. **Single env (`dev`)** común a todos los repos (cuenta AWS
   `681526276858`, region `us-east-1`). Staging/prod no entran en
   scope ahora.

## Consecuencias

**Positivas:**

- El monorepo distribuido puede evolucionar coordinadamente sin un
  "umbrella" repo que haga build monolítico.
- Cada repo mantiene ciclo de release propio (un cambio aislado en
  `orion-frontend` no fuerza deploy de `orion-cognitive-agent`).
- Bajo acoplamiento: un error en este agente no tumba el resto de los
  servicios.

**Negativas / riesgos:**

- Requiere disciplina manual en PRs que cruzan repos. Mitigable con
  un repo `orion-contracts` que publique un CHANGELOG centralizado
  (deuda abierta).
- El versionado semver obliga a decisiones MAJOR/MINOR/PATCH
  explícitas; el equipo es solo-dev, así que se aplican reglas laxas
  durante bootstrap (todo empieza en `0.1.0`).

## Próximos pasos

- [ ] Crear repo `orion-contracts` en `spark-match` o documentar
  schemas en este repo (decision deferred).
- [ ] Adoptar `release-please` o equivalente para CHANGELOG
  automatizado (decision deferred).
- [ ] Definir SLA de latencia entre agente ↔ backend ↔ frontend (Sprint
  de observabilidad).

## Revisores

- `@ahincho`.
