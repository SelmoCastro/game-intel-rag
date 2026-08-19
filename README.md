# Game Intel RAG

Assistente de IA para coletar, organizar e consultar informações públicas de vários jogos. O primeiro jogo integrado é **Hero Siege**, começando pela Season 10 — Ebontharn.

## O que já funciona

- coleta da notícia oficial pela RSS pública da Steam;
- normalização em `GameDocument`;
- deduplicação por hash;
- agente organizador com fallback determinístico;
- armazenamento local em SQLite;
- busca filtrada por jogo e temporada;
- agente de resposta com citações;
- API FastAPI;
- adaptador de bot Discord com `/ask`;
- testes automatizados.

O fallback local permite rodar o projeto sem chave de API. O agente organizador e o agente de resposta aceitam um cliente OpenRouter opcional via `OPENROUTER_API_KEY`.

## Executar localmente

```bash
uv venv
uv sync --extra dev
uv run pytest
uv run python cli.py ingest
uv run python cli.py ask "Quais novidades existem no Act 9?"
```

Banco local:

```text
data/game_intel.sqlite3
```

## API

```bash
uv run uvicorn app.api:app --reload
```

Healthcheck:

```bash
curl http://127.0.0.1:8000/health
```

Pergunta:

```bash
curl -X POST http://127.0.0.1:8000/ask \
  -H 'Content-Type: application/json' \
  -d '{"question":"Quais novidades existem no Act 9?","game":"Hero Siege","season":"Season 10"}'
```

## Discord

Configure o token sem colocá-lo no Git:

```bash
cp .env.example .env
# editar DISCORD_BOT_TOKEN
uv run python -m app.discord_bot
```

O bot oferece o comando `/ask`. A integração atual fixa Hero Siege Season 10 de propósito; o próximo passo é permitir a seleção segura de jogo e temporada.

## Arquitetura atual

```text
Steam RSS
   ↓
collector
   ↓
GameDocument
   ↓
OrganizerAgent (LLM opcional / fallback local)
   ↓
SQLite KnowledgeStore
   ↓
RetrievalService
   ↓
AnswerAgent
   ├── CLI
   ├── FastAPI
   └── Discord
```

## Próximas etapas

- separar coletores por jogo;
- adicionar mais fontes públicas;
- trocar recuperação lexical por embeddings + pgvector;
- gerar respostas com LLM usando contexto recuperado;
- adicionar avaliação com perguntas reais do grupo;
- permitir múltiplos jogos no Discord;
- orquestrar o fluxo com LangGraph somente após os componentes isolados estarem estáveis.

## Fontes atuais

- [Hero Siege — Ebontharn and Season 10](https://store.steampowered.com/news/app/269210/view/461208205952813643)

## Regra de coleta

O projeto usa fontes públicas e respeita limites e termos de uso. Não tenta contornar login, CAPTCHA, bloqueios ou mecanismos anti-bot.
