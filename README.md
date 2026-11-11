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

Os resultados são salvos como JSON em `data/runs/`. O cliente usa endpoint compatível com OpenAI Chat Completions. As investigações usam pesquisa web hospedada pela OpenAI via Responses API; as fontes retornadas são registradas para auditoria. Verifique fontes e referências antes de pontuar os resultados.

Consulte `docs/ARCHITECTURE.md` e `docs/EXPERIMENT.md` antes de interpretar os outputs.

## Pesquisa web

As investigações usam a pesquisa web hospedada pela OpenAI via Responses API. Por padrão, cada agente executa pesquisa e as fontes retornadas são guardadas nos resultados para auditoria. Isso gera chamadas e custos adicionais de API. Para desativar, defina RAVE_WEB_SEARCH=false no .env. A pesquisa requer RAVE_BASE_URL=https://api.openai.com/v1; endpoints compatíveis podem ser usados com pesquisa desativada. Confira se cada fonte sustenta a afirmação associada.
