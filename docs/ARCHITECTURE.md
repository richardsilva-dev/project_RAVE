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

## Limites

Esta versão não implementa navegação web, validação semântica da verdade, detecção de desinformação, propagação deliberada de erros, memória entre execuções, criação dinâmica de agentes ou infraestrutura distribuída. O cliente LLM não é, por si só, um navegador: fontes e referências precisam ser fornecidas por ferramentas externas ou pelo modelo e devem ser verificadas antes da avaliação.

## Provider

O cliente usa endpoint compatível com OpenAI Chat Completions. Configure endpoint, modelo e chave por variáveis de ambiente. Nenhuma chave deve ser commitada.
