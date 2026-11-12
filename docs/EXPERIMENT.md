# Execução experimental

Execute os mesmos enunciados em `single` e `hive`, mantendo modelo, ferramentas, contexto inicial e orçamento tão comparáveis quanto possível. O modo individual não recebe instrução deliberadamente enfraquecida.

Os resultados JSON são salvos em `data/runs/`. Compare precisão, cobertura, profundidade, completude, coerência, rastreabilidade, integração, ganho coletivo, tempo e custo. Não trate maior extensão como maior qualidade nem repetição como confirmação independente.

Prepare mapa de referência e rubrica independente antes de avaliar os outputs. O protótipo registra tokens informados pelo provedor, mas não calcula custo financeiro: tarifas dependem do modelo e precisam ser adicionadas à análise externa. O protótipo também não calcula pontuações automáticas nem cria gabarito.

## Perguntas do Evaluation Lab

1. A resposta coletiva supera a resposta de um agente individual em precisão, cobertura, completude e rastreabilidade, julgadas por avaliadores independentes?
2. A comunicação entre agentes acrescenta afirmações, relações ou evidências novas que não estavam nas contribuições iniciais?
3. O ganho observado justifica os tokens, a latência e a complexidade adicionais?

O modo `single` usa a pesquisa compartilhada e o mesmo modelo de raciocínio e contrato JSON do Hive. Isso melhora o controle inicial, mas não iguala o orçamento global: a colmeia faz mais chamadas. Defina e aplique um orçamento total comparável antes de usar custos/latência para concluir superioridade. Nas execuções, confira `metadata.calls`, incluindo modelo, finalidade, tokens, duração, estado e tentativas, e exclua execuções `PARTIAL`/`INVALID` de comparações de respostas completas.

## Comparação de estratégias de pesquisa

O modo padrão `shared_research` reproduz o fluxo centralizado da `main`. Na branch experimental, `RAVE_RESEARCH_MODE=independent_research` faz uma busca por agente. Relatórios devem usar a mesma pergunta e escopo, registrar os dois modos, conferir as fontes nos achados e separar eficiência operacional de qualidade factual. A comparação exploratória de 12/11/2026 está em `docs/RELATORIO_COMPARACAO_SHARED_VS_INDEPENDENT_2026-11-12.docx`.
