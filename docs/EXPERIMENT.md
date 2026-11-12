# Execução experimental

Execute os mesmos enunciados em `single` e `hive`, mantendo modelo, ferramentas, contexto inicial e orçamento tão comparáveis quanto possível. O modo individual não recebe instrução deliberadamente enfraquecida.

Os resultados JSON são salvos em `data/runs/`. Compare precisão, cobertura, profundidade, completude, coerência, rastreabilidade, integração, ganho coletivo, tempo e custo. Não trate maior extensão como maior qualidade nem repetição como confirmação independente.

Prepare mapa de referência e rubrica independente antes de avaliar os outputs. O protótipo registra tokens informados pelo provedor, mas não calcula custo financeiro: tarifas dependem do modelo e precisam ser adicionadas à análise externa. O protótipo também não calcula pontuações automáticas nem cria gabarito.

## Perguntas do Evaluation Lab

1. A resposta coletiva supera a resposta de um agente individual em precisão, cobertura, completude e rastreabilidade, julgadas por avaliadores independentes?
2. A comunicação entre agentes acrescenta afirmações, relações ou evidências novas que não estavam nas contribuições iniciais?
3. O ganho observado justifica os tokens, a latência e a complexidade adicionais?

O modo `single` usa a pesquisa compartilhada e o mesmo modelo de raciocínio e contrato JSON do Hive. Isso melhora o controle inicial, mas não iguala o orçamento global: a colmeia faz mais chamadas. Defina e aplique um orçamento total comparável antes de usar custos/latência para concluir superioridade. Nas execuções, confira `metadata.calls`, incluindo modelo, finalidade, tokens, duração, estado e tentativas, e exclua execuções `PARTIAL`/`INVALID` de comparações de respostas completas.
