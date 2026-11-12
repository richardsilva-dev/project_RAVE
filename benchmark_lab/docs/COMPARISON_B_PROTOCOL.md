# Comparação B — Open Deep Research

Upstream: https://github.com/langchain-ai/open_deep_research

## Regra de preservação

Usar o repositório oficial como submodule no repositório independente final. Fixar o SHA completo do commit; não acompanhar `main` automaticamente; preservar licença e lockfile; não modificar a implementação upstream para torná-la parecida com o RAVE.

## Preparação obrigatória

1. Clonar como submodule.
2. Registrar URL, SHA, data, licença e versão de Python.
3. Auditar dependências e lockfile.
4. Criar ambiente Python isolado.
5. Configurar modelos de pesquisa, sumarização, compressão e relatório.
6. Mapear os modelos para os modelos do RAVE quando suportados.
7. Registrar cada incompatibilidade de API ou modelo; não fazer fallback silencioso.
8. Desabilitar MCP, acesso a arquivos locais, terminal, escrita e exclusão, salvo necessidade documentada.
9. Executar apenas em loopback.
10. Fazer teste de fumaça sem usar perguntas oficiais do benchmark.

## Interpretação

Open Deep Research é uma referência externa de sistema completo, com supervisor e subagentes. Não é um baseline de agente único. A comparação B mede comportamento de sistemas diferentes e não isola causalmente o efeito de uma arquitetura coletiva.
