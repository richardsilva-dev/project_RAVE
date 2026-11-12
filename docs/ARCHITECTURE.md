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

O protocolo e seus limites estão em `docs/PROTOCOLO_CONFIABILIDADE.md`. Os estados são avaliações assistidas por modelo, não uma validação semântica automatizada. Qualidade metodológica, sindicância de fontes e suporte real do trecho à afirmação ainda exigem revisão.

## Limites

Esta versão implementa pesquisa web hospedada via Responses API, mas não implementa validação semântica da verdade, detecção de desinformação, memória entre execuções, criação dinâmica de agentes ou infraestrutura distribuída. As fontes retornadas devem ser verificadas para confirmar que sustentam as afirmações.

## Provider

O cliente usa endpoint compatível com OpenAI Chat Completions. Configure endpoint, modelo e chave por variáveis de ambiente. Nenhuma chave deve ser commitada.

## Pesquisa externa

As etapas iniciais dos agentes usam a ferramenta hospedada web_search da Responses API, com pesquisa obrigatória, e armazenam títulos e URLs retornados no resultado do agente. O Hive Core agrega fontes por URL e envia o catálogo para a síntese. Isso não valida semanticamente se cada fonte sustenta cada afirmação; essa revisão continua necessária. A pesquisa pode ser desativada com RAVE_WEB_SEARCH=false e exige o endpoint oficial OpenAI.
