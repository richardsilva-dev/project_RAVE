# Comparação A — protocolo de controle SOLO

## Pergunta metodológica

A arquitetura coletiva do RAVE acrescenta qualidade à resposta em relação a um único pesquisador, mantendo tão constantes quanto possível o modelo, a ferramenta de pesquisa, a pergunta, o escopo, o contexto inicial e o orçamento?

## Controle

- Uma única instância de `SoloResearchAgent`.
- Um único processo sequencial de decisão.
- Sem subagentes, supervisor, MessageBus, delegação ou colaboração.
- Mesmos identificadores de modelo do RAVE quando suportados.
- Mesma rota de pesquisa web hospedada e mesmo provedor, quando compatíveis.
- Mesma pergunta, escopo, idioma e contexto inicial.
- Limites explícitos de chamadas, tokens e duração.

## Limitação importante

O baseline desta pasta é uma implementação independente e sequencial. A equivalência não deve ser declarada até confirmar que o endpoint/modelo de pesquisa, a forma de uso de ferramentas, os parâmetros e os limites correspondem ao RAVE. A mesma etiqueta de modelo não garante condições idênticas se os parâmetros ou contextos forem diferentes.

## Orçamento

O código limita chamadas de pesquisa, chamadas de modelo, duração e tokens reportados. Como tokens de prompt só são conhecidos depois da resposta do provedor, o limite de tokens é verificado após cada chamada e a saída por chamada é limitada antecipadamente. Um experimento formal deve escolher limites que evitem ultrapassagem relevante e registrar qualquer overshoot.

Não comparar eficiência até fixar os limites e verificar o uso real de ambos os sistemas.
