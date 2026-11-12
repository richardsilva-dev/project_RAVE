# Estado da implementação do RAVE

Atualizado em 12/11/2026. Esta nota descreve o código nesta branch `independent_research` e as verificações executadas nesta revisão. A branch `main` não foi alterada.

## Implementado

- Mantém `shared_research` como modo padrão. A busca central é compartilhada pelos três agentes.
- Adiciona `independent_research` em duas fases: cada agente faz uma busca especializada com `RAVE_WEB_SEARCH_MODEL`; depois, os três analisam com o mesmo `RAVE_MODEL` usado no modo compartilhado.
- Mantém separadas as anotações de URLs retornadas pela ferramenta (`web_sources`) e URLs apenas escritas pelo modelo (`model_reported_references`). Ambas são referências para auditoria, não prova de confiabilidade ou suporte semântico.
- Preserva estado selecionado em caso de falha de busca compartilhada e libera a barreira de publicação quando uma busca independente falha.
- Registra timeouts como chamadas `FAILED`, com duração, tentativas e `agent_id`; chamadas feitas em threads preservam o contexto do agente.
- Preserva os achados iniciais se o refinamento falhar; o agente e o Hive ficam `PARTIAL`, inclusive quando o JSON de refinamento não pode ser reparado.
- Carrega a origem do provedor e o agente de origem da citação quando uma evidência passa entre agentes.
- Permite que `rave single --research-run-id` reutilize a pesquisa de um Hive compartilhado concluído com pergunta e escopo idênticos; falhas do baseline são persistidas como `PARTIAL` ou `INVALID`.
- CI de push inclui `main` e `independent_research`; PRs seguem direcionados a `main`.
- Adiciona testes para busca/análise em fases distintas, proveniência de citações, falha parcial e fluxo compartilhado.

## Verificação de código

`python -m pytest -q --tb=short`: 29 testes aprovados em 0,59 s nesta revisão.

As execuções reais v3 usaram a mesma pergunta e escopo, `gpt-5-search-api` para recuperação e `gpt-4.1-mini` para análise. O Hive independente e o Hive compartilhado terminaram `COMPLETED`. O baseline solo também terminou `COMPLETED` e reutilizou exatamente a pesquisa da execução compartilhada `rave-16dbc58f89dd`, validando pergunta e escopo. O par principal é `rave-16dbc58f89dd` / `single-164a2eb7912b`; duas execuções solo adicionais com a mesma entrada estão identificadas no registro. Métricas e proveniência estão em `data/comparisons/2026-11-12_experiment_v3.json`. Os registros brutos em `data/runs/` não são versionados.

A rodada independente v2 permanece `PARTIAL` por timeout. Seu registro antigo não contém telemetria para a chamada que expirou; a correção agora registra falhas de timeout com duração, tentativas e `agent_id`. Essa execução histórica não foi alterada retroativamente.

## Limites

O par compartilhado/solo reutiliza o mesmo material, mas ainda não teve avaliação humana cega. A rodada independente v3 concluiu, porém usa três buscas próprias e não deve ser comparada factual ou causalmente com o par de entrada compartilhada. Os rótulos de evidência, inclusive `SUPPORTED` e `CONFLICTING`, foram produzidos pelo modelo. Nenhuma afirmação ou fonte foi auditada manualmente nesta rodada. O total de URLs retornadas não mede independência editorial, confiabilidade nem se a página sustenta a afirmação.

Os tokens e a latência descrevem esta rodada e incluem fatores de reparo JSON e falhas; não estimam custo financeiro nem desempenho geral. Não houve orçamento global rigorosamente igualado, bateria com múltiplas perguntas ou avaliação estatística.

## Próximas etapas

1. Fazer comparações pareadas em várias perguntas e avaliações cegas com rubrica publicada antes das execuções.
2. Auditar manualmente origem, conteúdo, atualidade e suporte de uma amostra de afirmações e referências.
3. Definir e aplicar um orçamento de tokens/custo comparável antes de afirmar vantagem de eficiência.
