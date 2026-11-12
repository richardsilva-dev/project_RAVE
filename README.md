# RAVE — Hive Core 0.1

Protótipo experimental de inteligência coletiva com três agentes especializados, coordenação híbrida e comparação com um agente individual.

> Status: protótipo exercitado em execuções reais exploratórias. As rodadas v3 independente e compartilhada e o baseline individual foram concluídos. A rodada independente v2 terminou parcial por timeout. Ainda não há avaliação factual cega que demonstre superioridade de qualquer estratégia.

## Escopo implementado

- Três agentes especializados: fundamentos e evidências; mecanismos e relações; perspectivas e limitações.
- Hive Core com coordenação global e integração em camadas.
- Comunicação direta entre agentes, com barreira de publicação e registro das mensagens.
- Uma etapa de integração cruzada após a investigação inicial.
- Baseline de agente único e persistência JSON dos resultados.
- Testes automatizados dos contratos iniciais e da comunicação.
- Registro experimental por chamada, com modelo, finalidade, tokens, duração e tentativas; execuções parciais/inválidas são identificadas explicitamente.
- Baseline individual com pesquisa compartilhada, mesmo modelo de raciocínio e contrato de saída do Hive. Um orçamento global igual ainda precisa ser definido antes de comparar eficiência.
- Protocolo de confiabilidade informacional e rastreabilidade em `docs/PROTOCOLO_CONFIABILIDADE.md`.

## Requisitos e instalação

Python 3.11 ou superior.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -e .[dev]
cp .env.example .env
```

Preencha `RAVE_API_KEY` no arquivo `.env`. O aplicativo carrega esse arquivo ao iniciar. O endpoint, o modelo e os limites também podem ser alterados nele.

## Execução

```bash
rave single "Pergunta a investigar"
rave hive "Pergunta a investigar"
pytest
```

Para comparar o Hive com o agente individual usando exatamente a pesquisa de uma execução compartilhada concluída, reutilize seu ID:

```bash
rave single "Pergunta a investigar" --scope "Escopo idêntico ao da execução Hive" --research-run-id rave-ID_DA_EXECUCAO
```

O comando valida se o ID corresponde a uma execução `shared_research` concluída com a mesma pergunta e escopo. A pesquisa comum já registrada nessa execução não é repetida. Seu custo e duração ficam no registro Hive de origem; as chamadas do baseline individual ficam no registro `single`.

Os resultados são salvos como JSON em `data/runs/`. O cliente usa endpoint compatível com OpenAI Chat Completions. As investigações usam o modelo de pesquisa `gpt-5-search-api`; as fontes citadas são registradas para auditoria. Verifique fontes e referências antes de pontuar os resultados.

Consulte `docs/ARCHITECTURE.md` e `docs/EXPERIMENT.md` antes de interpretar os outputs.

## Pesquisa web

O modo padrão `RAVE_RESEARCH_MODE=shared_research` faz uma pesquisa web pela OpenAI via Chat Completions e `gpt-5-search-api`; os três agentes analisam a base compartilhada com o modelo configurado em `RAVE_MODEL`. Na branch `independent_research`, `RAVE_RESEARCH_MODE=independent_research` faz primeiro uma busca especializada por agente com o modelo de pesquisa e depois uma análise separada com o mesmo `RAVE_MODEL` usado no modo compartilhado. As anotações de URL retornadas pela ferramenta ficam separadas das URLs apenas escritas no JSON do agente. O modo e as fontes ficam registrados em cada execução. Para desativar a pesquisa, defina `RAVE_WEB_SEARCH=false`. A pesquisa requer `RAVE_BASE_URL=https://api.openai.com/v1`; citações do provedor não provam que uma fonte é confiável ou sustenta a afirmação.

## Limite de requisições

`RAVE_MAX_CONCURRENT_REQUESTS` controla quantas chamadas à API podem ocorrer ao mesmo tempo. O padrão é `1` para reduzir rajadas que podem atingir limites do provedor; aumente somente se os limites do projeto permitirem.
