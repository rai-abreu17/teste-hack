# Equipe operacional

Os modelos e esforços executáveis já estão definidos em `ROLE_DEFAULTS` de [orchestrate.mjs](../orchestrate.mjs). Estes arquivos acrescentam instruções de papel, sem criar uma segunda implementação do roteador.

| Papel / chave CLI | Modelo solicitado | Esforço | Instrução |
| --- | --- | --- | --- |
| Orquestrador / astra | gpt-6-astra | high | [astra.md](astra.md) |
| Investigador / investigator | claude-opus-5 | high | [investigator.md](investigator.md) |
| Engenheiro / engineer | gpt-5.6-sol | high | [engineer.md](engineer.md) |
| Pesquisador / researcher | claude-sonnet-5 | medium | [researcher.md](researcher.md) |

Use `--prompt-file .ai/agents/<papel>.md` com um pacote de contexto específico. Um modelo indisponível produz falha registrada; não existe fallback automático no executor.

O executor atual realiza análises textuais isoladas. Pesquisa com ferramentas, edição e experimentos devem receber tarefas separadas e ferramentas explicitamente adequadas; seus resultados são depois fornecidos nos contextos. O nome do papel não concede essas ferramentas. O teste de geometria não habilita, por si só, um pipeline autônomo de experimentação.
