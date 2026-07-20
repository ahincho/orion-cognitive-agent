<!-- =============================================================================
ORION Cognitive Agent — Pull Request Template
================================================================================
Single-main branching. PRs target `main`. Merge is `squash` only, and requires
`--admin` because the repo owner approves themselves (only owner).
-->

# Pull Request template — ORION Cognitive Agent

## Resumen

<!-- Breve descripcion del cambio (1-3 lineas). -->

## Tipo de cambio

Marcar con una `x`:

- [ ] Nueva feature (cambio que anade funcionalidad)
- [ ] Bug fix (cambio que corrige un issue)
- [ ] Refactor (cambio que no anade feature ni arregla bug)
- [ ] Docs (cambios solo en documentacion)
- [ ] Tests (anadir o mejorar tests)
- [ ] Chore (cambios operativos: deps, CI, configs, governance)

## Cambios

<!-- Lista detallada de los cambios principales -->

-
-
-

## Testing

<!-- Como verificaste los cambios -->

- [ ] `make install` corre sin errores
- [ ] `make qa` (ruff format + check + mypy) corre limpio
- [ ] `make test` (pytest) corre limpio
- [ ] Probado manualmente con `make run-local` (FastAPI + `/health`, `/ag-ui`)

## Checklist

- [ ] Mi PR solo toca archivos que estan bajo mi CODE OWN (`@ahincho`)
- [ ] He actualizado `README.md` si anadi o modifique funcionalidad publica
- [ ] He actualizado `AGENTS.md` si cambie convenciones operacionales
- [ ] Si agregue un nuevo patron operativo, he creado o actualizado el ADR
      correspondiente en `docs/architectural-decisions/`
- [ ] Mis commits siguen la convencion (`feat:`, `fix:`, `chore:`, etc.) + scope
- [ ] No hay secretos, keys ni valores de `ORION_AGENT_*` en el diff

## Notas para reviewers

<!-- Contexto adicional, capturas, links a issues, etc. -->

## Aprobaciones requeridas

Este PR es del autor unico (`@ahincho`). Como el autor no puede aprobar
su propio PR, el merge se realiza con `gh pr merge --admin` (escape-hatch
documentado en `AGENTS.md` y habilitado en el ruleset via
`current_user_can_bypass: always`).
