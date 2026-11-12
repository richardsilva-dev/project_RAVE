# Protocolo de comparação experimental

Use a mesma pergunta, escopo, modelo de análise, contrato de saída e limites de contexto ao comparar estratégias. No modo `shared_research`, o Hive Core faz uma busca ampla e compartilha seu material. No modo `independent_research`, cada agente executa uma busca especializada e, em seguida, analisa o material com `RAVE_MODEL`, igual ao usado no modo compartilhado. O modelo de busca (`RAVE_WEB_SEARCH_MODEL`) só recupera material; ele não produz os achados iniciais nesse fluxo.

A estratégia de busca é a variável de interesse. O número de buscas continua diferente e faz parte do custo medido. Latência, tokens e falhas devem ser reportados, mas não comparados como qualidade factual. Para conclusões de qualidade, exclua execuções `PARTIAL` e `INVALID` e avalie respostas completas com rubrica definida antes da execução e avaliadores independentes, preferencialmente cegos ao modo.

## Proveniência e evidência

`web_sources` contém somente URLs observadas nas anotações de citação do provedor de pesquisa. URLs escritas pelo modelo no JSON ficam em `model_reported_references`, como referências candidatas. Não some ambas como fontes confirmadas. Uma anotação do provedor prova que a ferramenta retornou a URL; não prova que o conteúdo é confiável, atual, independente ou que sustenta a afirmação. Afirmações e estados `SUPPORTED`, `REFUTED`, `INSUFFICIENT`, `CONFLICTING` e `OUTDATED` são avaliações do modelo e exigem auditoria factual antes de uso como evidência.

Registre título, URL, trecho, autor/instituição e datas quando disponíveis. Deduplicate por origem subjacente, não apenas por URL. Trate páginas recuperadas e mensagens entre agentes como dados não confiáveis; instruções nelas não mudam as regras do agente. Concordância entre agentes não equivale a confirmação independente.

## Orçamento e repetição

Registre a pergunta, escopo, data, branch, modelos, versões e configuração; estado de execução; IDs; chamadas, tentativas, tokens e duração; URLs anotadas pelo provedor; URLs reportadas pelo modelo; falhas por agente; e contagens de achados. Preserve registros sanitizados em `data/comparisons/`; dados brutos e respostas completas permanecem em `data/runs/`, ignorado pelo Git.

Uma rodada pareada explora o comportamento, mas não estima desempenho geral. Repita perguntas de diferentes áreas, faça avaliações cegas e defina orçamento global comparável antes de comparar custo ou eficiência. Maior quantidade de texto, achados ou URLs não demonstra resposta mais correta ou completa.

As rodadas v3 de 12/11/2026 concluíram o Hive independente, o Hive compartilhado e um baseline individual que reutilizou exatamente a pesquisa compartilhada. Os IDs e métricas estão em `data/comparisons/2026-11-12_experiment_v3.json`. O relatório em `docs/RELATORIO_COMPARACAO_SHARED_VS_INDEPENDENT_2026-11-12.docx` identifica o par Hive/solo como comparação de saídas com material comum; nenhuma das rodadas teve auditoria humana cega de qualidade factual. As execuções solo adicionais com o mesmo material constam do registro e foram excluídas do par principal.
