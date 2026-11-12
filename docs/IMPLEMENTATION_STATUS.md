# Estado da implementação — RAVE Hive Core

Atualizado em 12/11/2026. Este documento distingue código, testes automatizados e validação real com provedor.

## Implementado nesta branch `benchmark-preparation`

- Três agentes especializados e fixos, com comunicação direta, auditoria e barreira de publicação.
- Pesquisa web compartilhada, análise especializada, integração entre pares e síntese final.
- Evidência por afirmação, estados `SUPPORTED`, `REFUTED`, `INSUFFICIENT`, `CONFLICTING` e `OUTDATED`, preservação de origem e tratamento do conteúdo recuperado como dado não confiável.
- Registro por chamada de modelo, finalidade, modelo, tokens, duração e tentativas HTTP.
- Preservação das descobertas iniciais, mensagens recebidas, achados descartados e mudanças de refinamento.
- Classificação de execução como `COMPLETED`, `PARTIAL` ou `INVALID`.
- Validação completa do contrato de síntese: JSON válido, objeto raiz, todos os campos obrigatórios e tipos esperados.
- Síntese inválida agora define `synthesis_status=FAILED` e `execution_status=PARTIAL` quando há resultados de agentes preserváveis. A saída de fallback não é apresentada como resposta coletiva validada.
- Normalização canônica de URLs para deduplicar fragmentos, parâmetros de rastreamento conhecidos, host/porta/scheme em formas equivalentes. URLs originais são preservadas em `original_urls`.
- Contagem de URLs por achado baseada na URL canônica; isso continua sendo apenas um limite superior candidato de independência, não uma verificação da origem editorial.

## Evidência e validação

Os testes foram ampliados para cobrir JSON de síntese inválido/incompleto, classificação de execução parcial e deduplicação de variantes de URL. A execução desses testes precisa ser confirmada pelo GitHub Actions após a abertura do pull request. A integração disponível nesta sessão não retornou runs para o commit base; isso não equivale a um status de sucesso ou falha.

Nenhuma nova execução real com API foi realizada nesta etapa. Não inferir qualidade de pesquisa a partir dos testes unitários.

## Pendências antes do benchmark formal

1. Confirmar o resultado do workflow do GitHub Actions desta branch/PR.
2. Fazer uma execução real pequena e inspecionar `synthesis_status`, `execution_status`, URLs canônicas e `original_urls`.
3. Definir orçamento global comparável e rubrica antes da bateria experimental.
4. Executar o agente individual independente e configurar a referência Open Deep Research em laboratório isolado.
5. Realizar avaliação cega e auditoria de fontes antes de concluir superioridade.

## Limitações preservadas

Estados de evidência são avaliações assistidas por modelo, não verificação factual independente. URLs canônicas distintas podem reproduzir o mesmo documento. A contagem de fontes não demonstra diversidade editorial nem suporte semântico.
