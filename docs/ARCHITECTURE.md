# Arquitetura do RAVE Hive Core 0.1

## Modelo híbrido

O Hive Core formaliza a pergunta, cria três tarefas fixas, acompanha a execução e sintetiza o resultado. Os agentes investigam de forma especializada e trocam mensagens diretamente pelo MessageBus. O núcleo mantém o registro de auditoria sem ser intermediário obrigatório.

## Ciclo

1. Planejamento de três tarefas especializadas.
2. Investigação inicial paralela.
3. Compartilhamento direto de descobertas.
4. Barreira de publicação para garantir que todos os agentes tenham publicado antes de ler as caixas de entrada.
5. Uma etapa de integração cruzada por agente.
6. Integração local e cruzada das entregas.
7. Síntese global em um output único.
8. Persistência local dos resultados e metadados.

## Confiabilidade informacional

Descobertas incluem afirmações com estado de evidência, justificativa e metadados de origem. O conjunto de estados é `SUPPORTED`, `REFUTED`, `INSUFFICIENT`, `CONFLICTING` e `OUTDATED`. Mensagens entre agentes carregam IDs e evidências; repetição ou concordância não eleva o estado nem conta como confirmação independente. URLs distintas são apenas candidatas à independência porque podem reproduzir a mesma origem. Conteúdo recuperado e mensagens são dados não confiáveis e não podem alterar instruções dos agentes.

O protocolo e seus limites estão em `docs/PROTOCOLO_CONFIABILIDADE.md`. Os estados são avaliações assistidas por modelo, não uma validação semântica independente. Qualidade metodológica, sindicância de fontes e suporte real do trecho à afirmação ainda exigem revisão.

## Pesquisa externa

O cliente atual usa OpenAI-compatible Chat Completions. A busca web utiliza o modelo configurado em `RAVE_WEB_SEARCH_MODEL` (referência atual: `gpt-5-search-api`) com `web_search_options`; análise, integração e síntese usam `RAVE_MODEL` (referência atual: `gpt-4.1-mini`). As anotações `url_citation` são preservadas como URLs retornadas pelo provedor, não como prova de que a fonte sustenta a afirmação.

O Hive Core agrega fontes por URL canônica, removendo fragmentos e parâmetros conhecidos de rastreamento. As URLs originais observadas são preservadas para auditoria. URLs canônicas distintas ainda podem apontar para cópias da mesma origem subjacente.

A pesquisa pode ser desativada com `RAVE_WEB_SEARCH=false`. A pesquisa hospedada atual exige o endpoint oficial compatível configurado no ambiente.

## Estado da síntese e da execução

Uma resposta de síntese só é considerada concluída quando é JSON válido, objeto raiz e contém todos os campos obrigatórios com os tipos definidos. JSON inválido, incompleto ou com tipos incorretos resulta em `synthesis_status=FAILED` e `execution_status=PARTIAL` quando existem resultados de agentes preserváveis. Sem agentes concluídos, o estado é `INVALID`. Resultados parciais não devem ser pontuados como respostas completas.

## Limites

Esta versão registra metadados e instrui agentes a classificar e preservar evidências; não verifica automaticamente a qualidade metodológica, a identidade editorial, a independência entre publicações ou se um trecho sustenta semanticamente uma afirmação. A pesquisa compartilhada também significa que os três agentes podem começar da mesma base. Uma validação factual independente continua necessária.
