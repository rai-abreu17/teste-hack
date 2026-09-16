# Revisão do orquestrador

- Probes preliminares Astra, Opus e Sonnet receberam somente cálculo de volume. Ambos os Claude retornaram metadados com as versões exatas solicitadas; o JSONL do Codex não inclui o modelo. Flags e resultados ficam preservados.
- O primeiro invoke Sol não iniciou o modelo: a descoberta via where.exe corrompeu o caractere í do caminho. A falha original foi preservada em ../sol-cli-probe-20260913. A repetição usou o caminho explícito ao mesmo modelo, sem fallback.
- O probe Sol apresentou a conta de cobertura w²/900. Revisão do orquestrador encontrou uma hipótese geométrica que precisava ser explícita: os lados da projeção quadrada devem estar paralelos aos lados da caixa. Foi adicionada essa condição ao contexto do teste completo. A versão original continua no contexto arquivado do probe Sol.
- Probes são diagnóstico de conectividade. A aceitação final depende do workflow completo, de comparação matemática e de verificação dos arquivos preexistentes.
- Documentação consultada: https://learn.chatgpt.com/docs/config-file/config-reference ; https://learn.chatgpt.com/docs/non-interactive-mode ; https://code.claude.com/docs/en/model-config ; Context7 RPC resolve-library-id/query-docs arquivados neste diretório.
