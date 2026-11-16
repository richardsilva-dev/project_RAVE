# Execução experimental

Execute os mesmos enunciados em `single` e `hive`, mantendo modelo, ferramentas, contexto inicial e orçamento tão comparáveis quanto possível. O modo individual não recebe instrução deliberadamente enfraquecida.

## Orçamento global do piloto

A branch `benchmark-a-global-budget-guard` aplica um orçamento por execução antes de cada tentativa de rede, incluindo retries:
- Hive: 80.000 tokens, 3 tentativas de pesquisa, 12 chamadas de modelo, 180 segundos e US$ 0,50 estimados.
- O limite de chamadas conta tentativas e inclui chamadas de síntese/refinamento.
- A pesquisa compartilhada reserva 16.384 tokens adicionais para conteúdo fornecido pelo provedor, além do prompt local e da saída máxima configurada.
- O orçamento é registrado no campo `run_budget` do artefato JSON.
- Falha na pesquisa compartilhada interrompe a execução. Não há fallback silencioso para pesquisa individual dos agentes.

As tarifas de GPT-4.1-mini e a taxa de ferramenta de busca são configuradas conforme a tabela oficial. A tabela pública não apresenta uma tarifa de tokens específica para GPT-5 Search API; as duas variáveis `RAVE_SEARCH_INPUT_USD_PER_1M` e `RAVE_SEARCH_OUTPUT_USD_PER_1M` devem ser preenchidas explicitamente. Se os valores forem aproximados a partir de outra linha de modelo, isso deve ser declarado como hipótese metodológica.

O limite local de custo é uma estimativa, não um bloqueio de cobrança no provedor. O contexto de busca injetado pelo provedor é variável e pode ultrapassar a reserva. Configure um limite de gastos independente no projeto OpenAI.

## Avaliação

Compare precisão, cobertura, profundidade, completude, coerência, rastreabilidade, integração, ganho coletivo, tempo e custo. Não trate maior extensão como maior qualidade nem repetição como confirmação independente.

Prepare mapa de referência e rubrica independente antes de avaliar os outputs. Exclua execuções `PARTIAL`, `FAILED` ou `INVALID` de comparações de respostas completas. A primeira execução com orçamento serve como piloto de integração e não constitui, isoladamente, evidência de superioridade.

## Perguntas do Evaluation Lab

1. A resposta coletiva supera a resposta de um agente individual em precisão, cobertura, completude e rastreabilidade, julgadas por avaliadores independentes?
2. A comunicação entre agentes acrescenta afirmações, relações ou evidências novas que não estavam nas contribuições iniciais?
3. O ganho observado justifica os tokens, a latência e a complexidade adicionais?
