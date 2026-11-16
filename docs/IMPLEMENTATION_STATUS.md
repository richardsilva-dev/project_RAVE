# Estado da implementação — RAVE Hive Core

Atualizado em 13/11/2026. Esta branch experimental é separada da branch de produção. As alterações abaixo foram escritas no GitHub, mas ainda precisam de execução dos testes locais e de uma pesquisa real limitada antes de serem consideradas verificadas.

## Implementado nesta branch

- Três agentes especializados, comunicação direta, auditoria e integração em camadas.
- Pesquisa web compartilhada e síntese final.
- Guardião global de orçamento por execução, com reservas antes de cada tentativa de rede.
- Limites para tokens, buscas, chamadas de modelo (incluindo retries), tempo e custo estimado.
- Reserva conservadora de 16.384 tokens para contexto de pesquisa hospedada, além do prompt local e do máximo de saída.
- Reconciliação com tokens reportados pelo provedor e registro de custo estimado.
- Snapshot `run_budget` salvo no artefato da execução.
- Falha na pesquisa compartilhada agora interrompe o fluxo; os agentes não iniciam pesquisas individuais como fallback.
- Conteúdo recuperado continua tratado como evidência não confiável.

## Limitações

- A tarifa de tokens específica de GPT-5 Search API não aparece como linha separada na tabela pública de preços. As variáveis de preço precisam ser configuradas explicitamente e sua origem documentada.
- O limite de saída de análise por agente é 4.096 tokens; a síntese final tem limite separado de 8.192 tokens. Ambos consomem o mesmo orçamento global da execução.
- O limite de US$ 0,50 é estimado localmente, não imposto pelo provedor. O contexto interno de busca é variável. Configure um limite de gastos separado no OpenAI Platform.
- Validação offline no GitHub Actions concluída: 26 testes aprovados no commit `3b7a231515b63fa8caa4d8a4cbabc68d589b2a8b` (run `43922045558`). Nenhuma chamada de pesquisa paga foi realizada.
- Esta branch não altera `main`; ela deve ser testada antes de qualquer merge.
- Comparação B permanece bloqueada pelas pendências de segurança documentadas no laboratório.

## Próxima validação

1. Confirmar que a chave local é válida com a verificação não faturável `GET /models` do executor do laboratório.
2. Fazer uma única execução Hive com a pergunta e o escopo preservados da Comparação A.
3. Verificar `execution_status`, `run_budget`, tokens, custo estimado, chamadas, retries, duração e arquivos persistidos.
4. Só depois avaliar os outputs e decidir se a comparação é elegível.
