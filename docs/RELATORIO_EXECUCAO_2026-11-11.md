# Relatório de execução RAVE — 11/11/2026

## Objetivo

Investigar por que o RAVE não entregava uma resposta final e validar o fluxo completo: pesquisa dos três agentes, troca de informações e síntese integrada.

## Histórico e diagnóstico

- A falha anterior `credit_balance_exhausted` indicava ausência de crédito disponível naquele momento. Após a recarga, uma chamada mínima à API foi aceita; portanto, a conta passou a permitir chamadas pagas. O teste confirmou que havia saldo utilizável, mas não revelou o saldo exato.
- A pesquisa via Responses API no modelo configurado anteriormente recebeu `429 rate_limit_exceeded` com limite de tokens e tokens restantes insuficientes. Isso é rate limit temporário do modelo/projeto, diferente de crédito esgotado.
- A rota oficial de pesquisa por Chat Completions (`gpt-5-search-api`) foi validada com uma requisição real. A documentação da OpenAI especifica esse modelo para pesquisa via Chat Completions e citações em `message.annotations`.
- Na primeira tentativa Hive com a rota nova, o agente Fundamentos concluiu pesquisa em 12,8 s, mas os agentes seguintes receberam `429` com limite informado de 3.000 tokens e reset indicado em cerca de 370 s. A execução terminou antes de publicar todos os agentes e não produziu síntese. Esse resultado parcial não é uma resposta final válida.
- Em uma tentativa anterior, a execução foi interrompida antes de coletar uma saída final. Isso foi um encerramento prematuro durante o acompanhamento; não constitui evidência de erro interno do RAVE.

## Correções aplicadas

- Substituída a integração de pesquisa Responses pelo endpoint Chat Completions com `gpt-5-search-api`, usando o formato oficial de pesquisa e extraindo citações das anotações.
- O modelo de busca passou a usar `gpt-5-search-api` por padrão; `.env` local e `.env.example` foram alinhados. A chave não é incluída neste relatório.
- O retry de 429 respeita o maior intervalo entre `Retry-After` e o reset de tokens, inclusive esperas de até 420 s. O semáforo agora serializa a chamada e a respectiva espera para evitar que vários agentes repitam juntos.
- A aplicação registra progresso, duração das fases, fontes, mensagens e duração total no JSON de execução.
- README atualizado para descrever corretamente o modelo e endpoint de pesquisa.

## Verificações automatizadas

- `pytest`: **15 testes passaram** em 0,29 s, incluindo extração de citações, erros seguros, retry curto e longo, comunicação entre agentes e síntese simulada.
- O teste integrado simulado verifica três pesquisas, compartilhamento de mensagens e resposta consolidada. Isso comprova o fluxo de código, mas não substitui a chamada real ao provedor.

## Execução real integrada

Pergunta usada: “Quais são os benefícios, riscos e recomendações atuais para o uso de inteligência artificial generativa na educação? Compare fontes institucionais e apresente limites e divergências.”

- Duas tentativas intermediárias não foram aceitas como sucesso: uma terminou após rate limits longos; outra concluiu em 164,7 s, mas a auditoria encontrou zero achados estruturados, pois o parser aceitou objetos JSON fora do esquema. A síntese daquela tentativa não é considerada evidência válida.
- Execução final válida: `rave-86b64f402cfd`, salva em `data/runs/rave-86b64f402cfd.json`.
- Início: 15:45:51,9; conclusão: 15:49:12,4 (horário local do ambiente). Duração medida: **200,55 s** (3 min 20,6 s).
- Fases: busca web compartilhada 15,04 s; análise pelos três agentes e integração entre pares 167,30 s; integração local 0,0004 s; síntese final 18,20 s.
- Fluxo: 8 chamadas LLM no total (uma busca web, três análises iniciais, três integrações entre pares e uma síntese); **36 mensagens** trocadas; três agentes concluídos; **18 achados** (6 por agente); **8 fontes** compartilhadas e deduplicadas.
- Uso medido: 49.607 tokens de entrada + 26.160 de saída = **75.767 tokens**. O relatório não estima valor em dinheiro, pois os preços dependem do modelo e da conta. O volume alto é um ponto de eficiência a otimizar.
- Cada agente analisou a mesma base web compartilhada sob uma especialidade distinta (fundamentos/evidências; mecanismos/relações; perspectivas/limites), depois recebeu mensagens dos demais e refinou seus achados. Portanto, esta validação confirma pesquisa compartilhada, colaboração e síntese; ela não confirma três consultas web independentes.

### Resposta final produzida

> A inteligência artificial generativa (IAGen) na educação oferece benefícios importantes, como personalização da aprendizagem, redução da carga administrativa docente, democratização do acesso a recursos educacionais e promoção da inclusão e literacia em IA. Entretanto, apresenta riscos significativos, incluindo dependência cognitiva, comprometimento da integridade acadêmica, reprodução de vieses, questões de privacidade e segurança, além de limitações institucionais e impactos na saúde mental dos estudantes. Instituições como UNESCO e órgãos brasileiros recomendam regulamentação ética, validação pedagógica, formação docente, supervisão humana e governança institucional para o uso responsável da IAGen. A evidência empírica ainda é incipiente e heterogênea, com variações por nível de ensino, disciplina, infraestrutura e contexto cultural, o que gera divergências sobre usos permitidos e práticas regulatórias. A complementaridade entre perspectivas institucionais (normativas) e acadêmicas (empíricas) é essencial para um entendimento equilibrado e formulação de políticas eficazes.

### Características e avaliação

- A síntese organizou **4 benefícios, 6 riscos, 5 recomendações e 6 limitações/divergências**, conectando fundamentos, mecanismos e perspectivas.
- O RAVE integrou evidências e atribuiu contribuições aos agentes. As fontes incluem orientação institucional da UNESCO, orientação do Department for Education da Inglaterra e guia institucional da Unicamp. A UNESCO enfatiza abordagem centrada no ser humano, privacidade e validação pedagógica; o GOV.UK registra oportunidades de apoio ao trabalho docente e afirma que evidência sobre benefícios e riscos para estudantes ainda está emergindo; a Unicamp destaca revisão humana, proteção de dados e integridade acadêmica.
- A resposta cobre os principais lados da pergunta e preserva a incerteza sobre a evidência. Ainda assim, trata-se de uma execução exploratória: as fontes foram reunidas numa busca comum e reutilizadas pelos agentes, e as afirmações específicas devem ser conferidas nos documentos originais antes de uso decisório.
- **Completude relativa:** a execução final foi mais completa e auditável do que as tentativas anteriores, que não produziram uma resposta válida. Não foi executado um baseline de agente único com a mesma pergunta, fontes, modelo e limite de tokens; portanto, não há evidência experimental para afirmar que três agentes superam um agente único.
- **Eficiência:** a busca compartilhada evitou repetir a chamada web três vezes e contornou o limite observado no modelo de pesquisa. Porém, a execução final levou 3 min 20,6 s e consumiu 75.767 tokens; não se pode afirmar economia total de custo ou latência sem um baseline comparável.

### Fontes consultadas na execução

- [UNESCO — Guia para a IA generativa na educação e na pesquisa](https://www.unesco.org/pt/articles/guia-para-ia-generativa-na-educacao-e-na-pesquisa)
- [Department for Education (Inglaterra) — Generative artificial intelligence in education](https://www.gov.uk/government/publications/generative-artificial-intelligence-in-education/generative-artificial-intelligence-ai-in-education)
- [Unicamp — Guia de IA](https://inteligenciaartificial.unicamp.br/guia-de-ia-na-unicamp/)
- As outras cinco fontes e suas URLs estão registradas no JSON da execução.

## Fontes técnicas

- [Pesquisa web da API OpenAI](https://developers.openai.com/api/docs/guides/tools-web-search)
- [Limites de taxa da API OpenAI](https://developers.openai.com/api/docs/guides/rate-limits)
