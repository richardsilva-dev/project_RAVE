# Estado da implementação do RAVE

Atualizado em 12/11/2026. Esta nota descreve o código nesta branch `independent_research` e as verificações executadas nesta revisão. A branch `main` não foi alterada.

## Implementado

- Mantém `shared_research` como modo padrão. A busca central é compartilhada pelos três agentes.
- Adiciona `independent_research` em duas fases: cada agente faz uma busca especializada com `RAVE_WEB_SEARCH_MODEL`; depois, os três analisam com o mesmo `RAVE_MODEL` usado no modo compartilhado.
- Mantém separadas as anotações de URLs retornadas pela ferramenta (`web_sources`) e URLs apenas escritas pelo modelo (`model_reported_references`). Ambas são referências para auditoria, não prova de confiabilidade ou suporte semântico.
- Preserva estado selecionado em caso de falha de busca compartilhada e libera a barreira de publicação quando uma busca independente falha.
- CI de push inclui `main` e `independent_research`; PRs seguem direcionados a `main`.
- Adiciona testes para busca/análise em fases distintas, proveniência de citações, falha parcial e fluxo compartilhado.

## Verificação de código

`python -m pytest -q --tb=short`: 19 testes aprovados em 0,40 s nesta revisão.

As duas execuções reais v2 usaram a mesma pergunta e escopo, `gpt-5-search-api` para recuperação e `gpt-4.1-mini` para análise. A rodada compartilhada terminou `COMPLETED`; a independente terminou `PARTIAL` porque o agente 03 excedeu o tempo limite. Métricas e proveniência estão no relatório e em `data/comparisons/2026-11-12_shared_vs_independent_v2.json`. Os registros brutos em `data/runs/` não são versionados.

## Limites

A rodada independente parcial não permite comparar qualidade final das estratégias. A execução completa compartilhada não teve avaliação humana cega pareada. Os rótulos de evidência, inclusive `SUPPORTED`, foram produzidos pelo modelo. Nenhuma afirmação ou fonte foi auditada manualmente nesta rodada. O total de URLs retornadas não mede independência editorial, confiabilidade nem se a página sustenta a afirmação.

Os tokens e a latência descrevem esta rodada e incluem fatores de reparo JSON e falhas; não estimam custo financeiro nem desempenho geral. Não houve orçamento global rigorosamente igualado, bateria com múltiplas perguntas ou avaliação estatística.

## Próximas etapas

1. Repetir a execução independente até obter uma rodada completa, investigando o timeout do agente 03.
2. Fazer comparações pareadas em várias perguntas e avaliações cegas com rubrica publicada antes das execuções.
3. Auditar manualmente origem, conteúdo, atualidade e suporte de uma amostra de afirmações e referências.
4. Definir e aplicar um orçamento de tokens/custo comparável antes de afirmar vantagem de eficiência.
