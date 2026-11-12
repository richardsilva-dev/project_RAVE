# Estado da implementação — RAVE Hive Core

Atualizado em 12/11/2026. Este documento separa o que foi observado em execuções anteriores do que está implementado no código atual. As alterações recentes de instrumentação e baseline ainda não foram executadas contra o provedor.

## Implementado no código atual

- Três agentes especializados e fixos, com comunicação direta, auditoria e barreira de publicação.
- Pesquisa web compartilhada, análise especializada, integração entre pares e síntese final.
- Evidência por afirmação, estados `SUPPORTED`, `REFUTED`, `INSUFFICIENT`, `CONFLICTING` e `OUTDATED`, preservação de origem e tratamento do conteúdo recuperado como dado não confiável.
- Registro por chamada de modelo, finalidade, modelo, tokens de entrada/saída, duração e tentativas HTTP; totais da execução Hive incluem busca compartilhada, análises, reparos, refinamentos e síntese bem-sucedidos.
- Preservação das descobertas iniciais, mensagens recebidas, achados descartados e mudanças de refinamento, com razões quando fornecidas pelo modelo.
- Classificação do estado de execução como completa, parcial ou inválida. Uma execução parcial é salva explicitamente como `PARTIAL`, com falhas identificadas por agente; sem agentes concluídos, não é produzida uma síntese factual.
- Baseline individual atualizado para usar a mesma consulta de pesquisa compartilhada, modelo de raciocínio configurado e contrato JSON com validação/reparo; chamadas e tokens também são registrados.
- Validação estrutural dos campos e tipos dos resultados de agentes antes da integração, sem dependência adicional.

## Evidência de execução anterior

O relatório [RELATORIO_EXECUCAO_2026-11-11.md](RELATORIO_EXECUCAO_2026-11-11.md) registra 15 testes aprovados naquela revisão e uma execução real integrada válida, `rave-86b64f402cfd`, persistida em `data/runs/rave-86b64f402cfd.json`. Isso documenta o estado anterior à instrumentação atual; não é validação das mudanças listadas acima.

O experimento anterior concluiu com três agentes, 18 achados, 36 mensagens e 200,55 segundos. Não houve baseline individual pareado, mesma pergunta/fontes/condições, nem bateria comparativa. Portanto, não demonstra superioridade coletiva ou economia de recursos.

## Limitações e validações pendentes

- As alterações recentes ainda precisam de validação automatizada e de uma execução real.
- A correção do registro por chamada só poderá ser confirmada com uma nova execução; a execução histórica não guardou duração/modelo/finalidade de cada chamada.
- O baseline agora compartilha pesquisa, modelo de raciocínio e contrato, mas não existe ainda orçamento global de tokens rigorosamente igualado entre uma chamada individual e as várias chamadas Hive. Comparações de qualidade são mais controladas; comparações de eficiência ainda exigem protocolo de orçamento definido.
- Não foram realizados Evaluation Lab, avaliação independente, agente externo de referência ou comparação estatística.
- Estados de evidência são assistidos por modelo, não uma verificação semântica independente. Independência entre fontes e suporte real de trechos ainda precisam de auditoria.

## Próximos passos

1. Executar os testes automatizados e corrigir regressões.
2. Fazer uma execução Hive e uma baseline com pergunta e escopo idênticos; inspecionar chamadas, tokens, duração, estados de execução e rastreabilidade.
3. Definir orçamento global comparável e rubricar qualidade antes da bateria experimental.
4. Planejar avaliações independentes e estatísticas para responder se a colmeia melhora a qualidade, acrescenta informação por cooperação e a que custo/latência.
