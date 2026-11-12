# Arquitetura do RAVE Hive Core

## Modelo híbrido

O Hive Core planeja três tarefas fixas, acompanha os agentes, integra as contribuições e produz uma síntese. Os agentes comunicam descobertas diretamente pelo MessageBus. O núcleo registra a execução, mas não intermedeia cada mensagem.

## Ciclo de execução

1. Planejamento de três tarefas especializadas.
2. Pesquisa inicial dos agentes.
3. Compartilhamento direto das descobertas e barreira para publicação inicial.
4. Integração cruzada por agente.
5. Integração central das entregas e síntese.
6. Persistência dos resultados, evidências, mensagens e métricas de chamadas.

## Modos de pesquisa

`RAVE_RESEARCH_MODE=shared_research` é o padrão compatível com a arquitetura da `main`: o Hive Core faz uma busca web e entrega a mesma pesquisa aos três agentes, que analisam o conteúdo sob especialidades diferentes.

Na branch experimental `independent_research`, `RAVE_RESEARCH_MODE=independent_research` faz cada agente conduzir sua própria busca especializada antes da troca de descobertas. Esse modo aumenta o número de pesquisas e pode gerar fontes diferentes. A comparação registrada em `docs/RELATORIO_COMPARACAO_SHARED_VS_INDEPENDENT_2026-11-12.docx` é exploratória e não determina superioridade.

Ambos os modos usam `RAVE_WEB_SEARCH_MODEL` para busca e `RAVE_MODEL` para análise. As chamadas, modelos, finalidades, tokens, duração e tentativas ficam registradas por execução. Resultados de busca e conteúdo de páginas são dados não confiáveis; instruções embutidas não alteram as regras dos agentes.

## Confiabilidade informacional

Descobertas incluem afirmações com estado de evidência, justificativa e metadados de origem. Os estados são `SUPPORTED`, `REFUTED`, `INSUFFICIENT`, `CONFLICTING` e `OUTDATED`. Concordância entre agentes não é confirmação factual; repetição de uma mesma origem não conta como corroboração independente. URLs diferentes podem reproduzir a mesma publicação.

O protocolo está em `docs/PROTOCOLO_CONFIABILIDADE.md`. Os estados são avaliações assistidas por modelo, não validação semântica automatizada. A qualidade metodológica da fonte e seu suporte real à afirmação ainda precisam de auditoria.

## Falhas e estado da execução

Execuções são registradas como `COMPLETED`, `PARTIAL` ou `INVALID`. Resultados parciais preservam os agentes que concluíram e identificam falhas; não devem ser tratados como uma resposta coletiva completa. Se nenhum agente conclui, o Hive Core não produz uma síntese factual.

## Limites

O RAVE não verifica automaticamente a verdade, a independência das fontes ou se cada trecho sustenta semanticamente sua afirmação. O Evaluation Lab, as avaliações humanas independentes, o orçamento global rigorosamente comparável e os testes estatísticos continuam pendentes. A pesquisa web hospedada usa Chat Completions com `gpt-5-search-api`, requer o endpoint oficial OpenAI e pode ser desativada com `RAVE_WEB_SEARCH=false`.
