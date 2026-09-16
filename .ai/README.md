# BoxFlow multi-agent runner

Estado atual: a arbitragem `009-astra` concluiu o teste integral reaproveitando as seis etapas válidas. A missão M-001 de investigação foi iniciada. Consulte [STATE.md](STATE.md) antes de executar qualquer tarefa. As falhas anteriores permanecem no histórico.

Para retomar somente o que falta, depois de o provedor liberar o uso:

```powershell
node .ai/orchestrate.mjs smoke --context .ai/smoke-context.md --run-id smoke-20260913-verified --cross-review --resume
```

Não criar um novo run para repetir as seis etapas concluídas. `--resume` verifica prompt, contexto, modelo, esforço e integridade da resposta contra o stream original; alterações incompatíveis interrompem a retomada. As falhas históricas são preservadas.

## Estrutura de P&D

- [Regras centrais](ORCHESTRATION.md) e [novo briefing](RD-BRIEF.md): instruções do usuário preservadas.
- [Problema e missão M-001](problem.md): primeira reavaliação real, pendente do gate de infraestrutura.
- [Papéis](agents/README.md): roteamento e instruções de cada agente.
- [Inventário](evidence/inventory.md) e [fontes](research/source-index.md): trabalho existente a reutilizar.
- [Hipóteses](hypothesis-register.md), [experimentos](experiments/experiment-matrix.md) e [decisões](decision-log.md): registros canônicos.
- [Debate real do smoke](debates/smoke-review.md) e [estado das revisões](reviews/status.md).

Os experimentos antigos da aplicação não foram reexecutados nesta configuração. O teste geométrico da infraestrutura usa condições próprias e não valida o sensor físico ou a arquitetura MVP.

This directory contains a real CLI orchestrator for the locally installed Codex and Claude CLIs. It invokes exact requested model names and never substitutes a fallback model. Every subprocess receives a fresh, minimal prompt in a temporary working directory outside the repository, with shell expansion disabled.

## Single invocation

The four standard roles have pinned defaults:

| Role | CLI | Requested model | Effort |
|---|---|---|---|
| `astra` | Codex | `gpt-6-astra` | high |
| `engineer` | Codex | `gpt-5.6-sol` | high |
| `investigator` | Claude | `claude-opus-5` | high |
| `researcher` | Claude | `claude-sonnet-5` | medium |

```powershell
node .ai/orchestrate.mjs invoke `
  --role engineer `
  --context .ai/smoke-context.md `
  --prompt "Assess the implementation and propose validation." `
  --run-id manual-engineer-001
```

Custom roles must supply `--provider`, `--model`, and `--effort`. Use `--prompt-file` when the role instruction is long. `--timeout-ms` defaults to ten minutes.

## Smoke workflow

```powershell
node .ai/orchestrate.mjs smoke `
  --context .ai/smoke-context.md `
  --run-id smoke-2026-09-13
```

The workflow runs an Astra plan, then three specialists independently with the same task and plan, and finally Astra arbitration. Add `--cross-review` for an anonymous engineer↔investigator critique before arbitration; the Sonnet researcher remains an independent evidence organizer. Calls are intentionally sequential so local authentication or credential prompts cannot overlap; the specialist round remains blind because no specialist sees peer output.

## Logs and state

Each run is stored under `.ai/runs/<run-id>/`. Every numbered invocation directory contains:

- `metadata.json`: run ID, timestamp, agent, provider, requested and observed model, effort, prompt/context hashes and files, resolved native command, argument array, exit code, duration, status, and failure reasons;
- `prompt.txt` and `context.txt`: exact isolated inputs;
- `stdout.jsonl` and `stderr.log`: unmodified process streams, including partial output after a timeout;
- `result.md`: validated final response with the protocol marker removed.

`manifest.json` summarizes the run. Unless `--no-state` is supplied, `.ai/STATE.md` is atomically refreshed with `CURRENT_RUN`, `CURRENT_PHASE`, `ACTIVE_HYPOTHESES`, `COMPLETED_TASKS`, `PENDING_TASKS`, `FAILED_TASKS`, and `NEXT_ACTION`. Metadata is first written with `status: starting`, then replaced after validation, so abrupt termination still leaves an attributable record.

On Windows, the runner reads the npm shim and invokes its underlying Node script or native executable directly. It does not interpolate prompts into a shell command. A timeout kills the Windows process tree and retains output received before termination.

The runner treats exit code zero as only one check. It fails on CLI startup errors, nonzero exits (including authentication or unavailable-model errors), timeouts, malformed JSON streams, missing protocol completion, empty output, a missing completion marker, ambiguous reported models, or a reported model that differs from the request. Claude currently reports its model in stream JSON. Codex CLI versions that omit a model field are logged as `observedModel: null` with `observedModelSource: not-reported-by-cli`; the exact requested model remains auditable in `argv`. If Codex reports a model, equality is enforced. This is a CLI observability limit, not proof that a requested model exists or that the service honored it.

No CLI can guarantee the factual quality of a response. The completion marker catches common truncation and instruction failures but cannot prove semantic completeness. Claude runs in safe mode with slash commands and hooks disabled, a minimal system prompt, `--tools ''`, and an empty strict MCP configuration. Codex `exec` is run in an empty temporary directory with ephemeral state, a read-only sandbox, approvals disabled, user config ignored, host skill discovery/plugins/MCP disabled, project instructions capped at zero bytes, and repository checks skipped. Codex still has built-in agent capabilities; the external empty directory and read-only sandbox are additional isolation boundaries.

## Tests

```powershell
node --test .ai/test/orchestrate.test.mjs
```

Tests use the explicitly named fake fixture in `.ai/test/fixtures/`. They verify runner control flow and failure handling only; they are not evidence that any real model is present or callable.

Claude can report auxiliary model usage generated by its own CLI. `modelUsage` and `auxiliaryModels` preserve that evidence separately from the primary answer model. The initial Opus smoke recorded auxiliary Haiku usage; it was not a substitute author or an independent investigator. Later calls disable nonessential traffic and terminal-title generation through per-process environment settings.

The current runner stops on usage limits and records `USAGE_LIMIT` for new attempts. It does not switch providers/models, purchase credits, or automatically wait and retry. Research tools and experiment execution are separate tasks; the text-only smoke cannot stand in for either.
