# Game Intel RAG — Roadmap de Implementação

> **Para o Hermes:** executar fase por fase, validando cada marco antes de avançar.

**Objetivo:** construir um assistente de IA para consultar informações atualizadas de vários jogos, começando por Hero Siege Season 10, com fontes citadas, controle de temporada/patch e integração futura com Discord.

**Arquitetura:** pipeline de ingestão determinístico para coletar fontes públicas; agentes com LLM apenas para interpretar, classificar e responder; RAG com filtros por jogo, temporada e patch; bot Discord como interface.

**Stack inicial:** Python 3.12, Pydantic, HTTPX, BeautifulSoup, PostgreSQL, pgvector, embeddings, OpenRouter/Ollama, FastAPI, LangGraph somente na etapa de orquestração, Discord.py e Docker.

---

## Estado atual

Repositório: `https://github.com/SelmoCastro/game-intel-rag`

Já implementado:

- contrato `GameDocument` em `app/models.py`;
- coletor RSS oficial da Steam em `app/collectors.py`;
- persistência local em `app/storage.py`;
- coleta da notícia da Season 10 de Hero Siege;
- testes básicos: `4 passed`;
- README e ambiente com `uv`.

Ainda não implementado:

- agente organizador;
- banco vetorial;
- embeddings;
- RAG;
- agente de resposta;
- bot Discord;
- avaliação automática.

## Regras de arquitetura

1. **Scraping não será delegado ao LLM.** Coleta, parsing, retry e rate limit devem ser previsíveis.
2. **Todo documento terá fonte e metadados.** Resposta sem fonte não é considerada pronta.
3. **Temporada e patch são filtros, não apenas texto do embedding.**
4. **O LLM deve retornar estruturas validadas por Pydantic.**
5. **O sistema deve admitir ausência de evidência.** Nunca preencher lacunas inventando.
6. **Começar com Hero Siege, mas manter `game` configurável.**
7. **Cada fase termina com teste automatizado e demonstração reproduzível.**

---

# Fase 0 — Fundação e contrato de dados

**Objetivo:** deixar claro o que entra no sistema e garantir que dados de jogos diferentes possam coexistir.

### Tarefas

1. Revisar `GameDocument` e adicionar campos necessários:
   - `document_id` determinístico;
   - `game_slug`;
   - `season_slug`;
   - `source_priority`;
   - `content_hash`;
   - `updated_at`.
2. Criar enums para fonte e categoria.
3. Criar validação de URLs e conteúdo mínimo.
4. Adicionar testes para documentos duplicados, documentos antigos e campos inválidos.
5. Definir política de deduplicação por `source_url + content_hash`.

### Arquivos

- Modificar: `app/models.py`
- Criar: `app/identifiers.py`
- Modificar: `tests/test_documents.py`
- Criar: `tests/test_identifiers.py`

### Marco de saída

- Dois documentos de jogos diferentes podem ser validados pelo mesmo modelo.
- Documento sem fonte ou conteúdo é rejeitado.
- Documento repetido possui o mesmo identificador.

---

# Fase 1 — Ingestão de fontes públicas

**Objetivo:** coletar documentos de forma repetível, com retry, timeout, rate limit e preservação da fonte original.

### Tarefas

1. Extrair uma interface comum para coletores:

```python
class SourceCollector(Protocol):
    def collect(self) -> list[GameDocument]: ...
```

2. Separar o coletor Hero Siege da lógica genérica:
   - `app/collectors/steam_rss.py`;
   - `app/collectors/hero_siege.py`.
3. Adicionar coletor de patch notes.
4. Salvar o conteúdo bruto em `data/raw/`.
5. Implementar retry limitado e logs sem expor segredos.
6. Implementar deduplicação antes da persistência.
7. Criar comando:

```bash
uv run python -m app.cli collect --game hero-siege
```

### Arquivos

- Criar: `app/collectors/base.py`
- Criar: `app/collectors/steam_rss.py`
- Criar: `app/collectors/hero_siege.py`
- Criar: `app/cli.py`
- Criar: `tests/test_collectors.py`

### Marco de saída

- O comando coleta a fonte oficial sem duplicar documentos.
- Um erro de rede gera mensagem clara e não corrompe os dados existentes.
- Toda notícia salva mantém URL, origem e data de coleta.

### Limite

Não coletar conteúdo que exija login, CAPTCHA ou bypass anti-bot. Priorizar Steam RSS, notas oficiais, wiki pública e APIs permitidas.

---

# Fase 2 — Agente organizador

**Objetivo:** transformar texto bruto em unidades pesquisáveis e metadados confiáveis.

O agente organizador será o primeiro componente que usa LLM. Ele não fará scraping.

### Fluxo

```text
texto bruto
  ↓
chunking por seção
  ↓
LLM com saída estruturada
  ↓
Pydantic valida
  ↓
documentos organizados
```

### Tarefas

1. Criar schema `OrganizedDocument`.
2. Criar prompt versionado em `app/agents/prompts/organizer_v1.txt`.
3. Criar cliente LLM compatível com OpenRouter e Ollama.
4. Implementar fallback quando o LLM retornar JSON inválido.
5. Adicionar classificação por:
   - patch;
   - temporada;
   - classe;
   - item;
   - boss;
   - build;
   - sistema do jogo.
6. Registrar modelo, prompt version e tempo de execução.
7. Criar fixture de texto da Season 10 para testes sem custo de API.

### Arquivos

- Criar: `app/agents/organizer_agent.py`
- Criar: `app/agents/llm_client.py`
- Criar: `app/agents/prompts/organizer_v1.txt`
- Criar: `app/models/organized_document.py`
- Criar: `tests/test_organizer.py`
- Criar: `tests/fixtures/hero_siege_season_10.txt`

### Marco de saída

Dado um texto sobre a Season 10, o sistema produz documentos estruturados e rejeita respostas que não respeitem o schema.

---

# Fase 3 — Banco de conhecimento

**Objetivo:** substituir JSON local por armazenamento persistente e pesquisável.

### Tarefas

1. Criar `docker-compose.yml` com PostgreSQL e pgvector.
2. Criar tabelas para:
   - fontes;
   - documentos;
   - chunks;
   - embeddings;
   - execuções de agentes.
3. Criar migrations ou inicialização idempotente.
4. Implementar upsert por `document_id` e `content_hash`.
5. Criar filtros por `game_slug`, `season_slug`, `patch` e categoria.
6. Testar persistência e reprocessamento sem duplicatas.

### Arquivos

- Criar: `docker-compose.yml`
- Criar: `app/db/connection.py`
- Criar: `app/db/schema.sql`
- Criar: `app/db/repository.py`
- Criar: `tests/test_repository.py`

### Marco de saída

O mesmo documento pode ser processado duas vezes sem criar duplicata e pode ser consultado filtrando por jogo e temporada.

---

# Fase 4 — Embeddings e recuperação híbrida

**Objetivo:** recuperar informação relevante sem perder precisão por versão do jogo.

### Tarefas

1. Criar serviço de embeddings com interface para OpenRouter/Ollama.
2. Armazenar vetores no pgvector.
3. Implementar busca semântica.
4. Implementar busca textual por palavras-chave.
5. Combinar as duas buscas.
6. Priorizar:
   - jogo correto;
   - temporada atual;
   - patch mais recente;
   - fonte oficial;
   - conteúdo mais novo.
7. Retornar trechos e metadados, nunca apenas texto solto.

### Arquivos

- Criar: `app/rag/embeddings.py`
- Criar: `app/rag/retriever.py`
- Criar: `app/rag/ranking.py`
- Criar: `tests/test_retriever.py`

### Marco de saída

Perguntas sobre Hero Siege Season 10 retornam os trechos corretos e não priorizam documentos antigos quando existe informação mais nova.

---

# Fase 5 — Agente de resposta

**Objetivo:** responder perguntas dos jogadores usando apenas o contexto recuperado.

### Fluxo

```text
pergunta
  ↓
identificação de jogo/temporada
  ↓
retriever
  ↓
contexto com fontes
  ↓
LLM
  ↓
resposta validada
```

### Tarefas

1. Criar schema `Answer` com resposta, fontes, confiança e aviso.
2. Criar prompt defensivo.
3. Recusar afirmações quando o contexto for insuficiente.
4. Implementar citações clicáveis.
5. Informar quando o documento mais recente for antigo.
6. Adicionar logging de latência, tokens e custo.
7. Criar conjunto inicial de 20 perguntas reais do grupo.

### Arquivos

- Criar: `app/agents/answer_agent.py`
- Criar: `app/agents/prompts/answer_v1.txt`
- Criar: `app/models/answer.py`
- Criar: `tests/test_answer_agent.py`
- Criar: `tests/fixtures/evaluation_questions.json`

### Marco de saída

O agente responde no terminal, cita as fontes e diz explicitamente quando não possui dados suficientes.

---

# Fase 6 — Avaliação e observabilidade

**Objetivo:** medir se o sistema é realmente útil, em vez de apenas parecer convincente.

### Métricas

- precisão da recuperação;
- presença de fonte;
- correção da temporada/patch;
- taxa de resposta sem evidência;
- latência;
- tokens e custo;
- respostas avaliadas como alucinação.

### Tarefas

1. Criar dataset com perguntas e respostas esperadas.
2. Criar teste de regressão do RAG.
3. Criar avaliação manual com respostas do grupo.
4. Registrar traces de coleta, organização, recuperação e resposta.
5. Comparar prompt e modelo sem perder histórico.

### Arquivos

- Criar: `app/evaluation/dataset.py`
- Criar: `app/evaluation/run.py`
- Criar: `app/evaluation/report.py`
- Criar: `tests/test_evaluation.py`

### Marco de saída

Existe um relatório reproduzível mostrando quais perguntas o sistema responde bem e onde falha.

---

# Fase 7 — API e bot Discord

**Objetivo:** disponibilizar o sistema para o grupo sem misturar interface com lógica do RAG.

### Tarefas

1. Criar API FastAPI:
   - `POST /ask`;
   - `POST /ingest` protegido;
   - `GET /health`.
2. Validar entrada, limite de tamanho e erros.
3. Criar bot Discord com comando `/ask`.
4. Formatar respostas com fontes e patch.
5. Implementar rate limit por usuário.
6. Manter tokens somente em `.env` ou Secrets.
7. Criar Dockerfile e healthcheck.

### Arquivos

- Criar: `app/api/main.py`
- Criar: `app/bot/discord_bot.py`
- Criar: `app/bot/formatters.py`
- Criar: `Dockerfile`
- Criar: `tests/test_api.py`
- Criar: `tests/test_bot_formatters.py`

### Marco de saída

Um amigo consegue perguntar no Discord e receber resposta com fonte, sem acessar o servidor ou o banco diretamente.

---

# Fase 8 — Agente orquestrador com LangGraph

**Objetivo:** coordenar o fluxo completo somente quando os componentes isolados já estiverem testados.

### Grafo proposto

```text
entrada
  ↓
classify_question
  ↓
select_game_and_patch
  ↓
retrieve_context
  ↓
check_evidence
  ├── insuficiente → ask_clarification / refuse
  └── suficiente  → generate_answer
                         ↓
                    cite_sources
```

### Tarefas

1. Criar estado tipado do grafo.
2. Transformar cada etapa existente em nó.
3. Definir transições explícitas.
4. Adicionar timeout e limite de iterações.
5. Persistir trace do grafo.
6. Comparar resultado do grafo com o pipeline direto.

### Arquivos

- Criar: `app/agents/state.py`
- Criar: `app/agents/graph.py`
- Criar: `tests/test_graph.py`

### Marco de saída

O grafo não muda o comportamento correto do sistema e melhora apenas a coordenação, a rastreabilidade ou a extensibilidade.

---

# Fase 9 — Segundo jogo

**Objetivo:** provar que a arquitetura é realmente genérica.

### Tarefas

1. Escolher o segundo jogo.
2. Criar `app/collectors/<game_slug>.py`.
3. Reutilizar `GameDocument`, organização, RAG e bot.
4. Adicionar filtros e testes específicos do novo jogo.
5. Confirmar que uma pergunta de um jogo não recupera documentos de outro.

### Marco final

O mesmo bot responde sobre dois jogos sem duplicar a arquitetura central.

---

# Ordem de execução recomendada

```text
Fase 0 → Fase 1 → Fase 2 → Fase 3 → Fase 4
                                      ↓
                              Fase 5 → Fase 6
                                      ↓
                              Fase 7 → Fase 8
                                      ↓
                              Fase 9
```

Não iniciar Discord, LangGraph ou múltiplos agentes antes de o RAG responder corretamente no terminal.

# Critério de pronto do projeto

O projeto será considerado demonstrável quando:

- coletar dados públicos de pelo menos duas fontes;
- organizar documentos por jogo, temporada e patch;
- responder 20 perguntas de teste;
- citar fontes em todas as respostas factuais;
- avisar quando não houver evidência atual;
- funcionar via API e Discord;
- possuir Docker, testes e README reproduzível;
- adicionar um segundo jogo sem reescrever o núcleo.
