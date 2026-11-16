# RAVE — Hive Core 0.1

Protótipo experimental de inteligência coletiva com três agentes especializados, coordenação híbrida e comparação com um agente individual.

> Status: implementação experimental. A hipótese de superioridade da colmeia permanece aberta; esta branch acrescenta guardas locais de orçamento e ainda precisa passar pelos testes locais e por uma execução piloto controlada.

## Escopo implementado

- Três agentes especializados: fundamentos e evidências; mecanismos e relações; perspectivas e limitações.
- Hive Core com coordenação global e integração em camadas.
- Comunicação direta entre agentes, com barreira de publicação e registro das mensagens.
- Uma etapa de integração cruzada após a investigação inicial.
- Pesquisa web compartilhada; falha na pesquisa compartilhada agora interrompe a execução, sem fallback silencioso para pesquisas individuais.
- Registro por chamada, tokens, duração, tentativas, custo estimado e snapshot do orçamento global.
- Limites globais de tokens, buscas, chamadas de modelo (incluindo retries), tempo e custo estimado.

## Instalação

Python 3.11 ou superior.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -e .[dev]
cp .env.example .env
```

Preencha `RAVE_API_KEY` e as duas variáveis de preço do GPT-5 Search API no arquivo `.env`. Não versione esse arquivo.

## Orçamento do piloto

Os limites iniciais são 80.000 tokens, 3 tentativas de pesquisa, 12 chamadas de modelo, 180 segundos e US$ 0,50 estimados por execução. O limite de buscas/chamadas conta retries. As reservas são feitas antes da chamada de rede. Para pesquisa hospedada, o cálculo reserva 16.384 tokens adicionais de contexto, além do texto local e do máximo de saída.

A tabela pública da OpenAI não apresenta uma linha de tarifa de tokens específica para GPT-5 Search API. Por isso, as variáveis `RAVE_SEARCH_INPUT_USD_PER_1M` e `RAVE_SEARCH_OUTPUT_USD_PER_1M` são obrigatórias e precisam ser preenchidas com os valores aplicáveis no painel de cobrança. Se usar tarifa de outro modelo como aproximação, registre isso como hipótese, não como tarifa confirmada. O cálculo local não é um teto de cobrança do provedor; mantenha também um limite de gastos no projeto OpenAI.

## Execução

```bash
rave hive "Pergunta a investigar"
pytest
```

Os resultados são salvos como JSON em `data/runs/`, incluindo `run_budget` com limites, consumo, reservas e saldo estimado. Uma execução que falhe na pesquisa compartilhada não continua para os agentes. Execuções parciais ou falhas não são resultados comparáveis completos.

Consulte `docs/ARCHITECTURE.md` e `docs/EXPERIMENT.md` antes de interpretar os outputs.
