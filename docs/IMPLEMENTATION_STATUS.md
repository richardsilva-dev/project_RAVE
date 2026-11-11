# Estado da implementação — Hive Core 0.1

## Implementado no repositório

- Estrutura Python com configuração por ambiente e arquivo `.env.example`.
- Contratos tipados para tarefas, descobertas, evidências, mensagens, resultados e metadados.
- Classe-base comum para os três agentes.
- Três especializações fixas: fundamentos/evidências; mecanismos/relações; perspectivas/limitações.
- MessageBus em memória com mensagens diretas, auditoria e barreira de publicação para sincronizar a troca inicial.
- Execução paralela das investigações, com pesquisa web via Responses API, seguida de uma etapa de integração cruzada.
- Hive Core com planejamento, integração de contribuições e síntese final.
- Baseline de agente único.
- Persistência local de resultados em JSON.
- CLI com comandos `rave single` e `rave hive`.
- Testes unitários iniciais e workflow de CI com pytest.

## Ainda não implementado


- Rubrica de avaliação automática, mapa de referência, pontuação ou comparação estatística.
- Contabilidade financeira automática de custos; tokens reportados pelo provedor são registrados.
- Reinvestigação direcionada pelo Hive Core.
- Tratamento avançado de falhas, validação semântica, detecção de desinformação ou propagação deliberada de erros.

## Validação

Os arquivos e o workflow de testes foram adicionados ao GitHub. A execução local dos testes e uma execução real com provedor de modelo ainda precisam ser realizadas. O estado de CI não foi confirmado no momento deste registro.

## Próximos passos técnicos

1. Executar `pip install -e ".[dev]"` e `pytest -q` em ambiente Python 3.11+.
2. Corrigir qualquer falha de instalação ou teste observada.
3. Confirmar acesso ao modelo de pesquisa configurado e comparar o orçamento de busca entre agente único e colmeia.
4. Executar um caso pequeno de ponta a ponta e inspecionar mensagens, descobertas, síntese e metadados.
5. Só então preparar a primeira bateria comparativa.
