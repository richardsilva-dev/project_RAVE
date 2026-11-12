# RAVE — Hive Core 0.1

Protótipo experimental de inteligência coletiva com três agentes especializados, coordenação híbrida e comparação com um agente individual.

> Status: primeira implementação em construção e ainda não validada em execução real. A hipótese de superioridade da colmeia permanece aberta.

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

Os resultados são salvos como JSON em `data/runs/`. O cliente usa endpoint compatível com OpenAI Chat Completions. As investigações usam o modelo de pesquisa `gpt-5-search-api`; as fontes citadas são registradas para auditoria. Verifique fontes e referências antes de pontuar os resultados.

Consulte `docs/ARCHITECTURE.md` e `docs/EXPERIMENT.md` antes de interpretar os outputs.

## Pesquisa web

O Hive faz uma pesquisa web compartilhada pela OpenAI via Chat Completions e `gpt-5-search-api`. Os três agentes analisam o conjunto citado em suas especialidades, compartilham descobertas e passam pela síntese final. Essa abordagem reduz chamadas repetidas e respeita limites de taxa mais baixos. As citações são guardadas nos resultados para auditoria. Para desativar, defina `RAVE_WEB_SEARCH=false` no `.env`. A pesquisa requer `RAVE_BASE_URL=https://api.openai.com/v1`; endpoints compatíveis podem ser usados com pesquisa desativada. Confira se cada fonte sustenta a afirmação associada.

## Limite de requisições

`RAVE_MAX_CONCURRENT_REQUESTS` controla quantas chamadas à API podem ocorrer ao mesmo tempo. O padrão é `1` para reduzir rajadas que podem atingir limites do provedor; aumente somente se os limites do projeto permitirem.
