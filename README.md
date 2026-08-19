# Hero Siege RAG Bot

Projeto de portfólio para coletar, organizar e consultar informações públicas de **Hero Siege**, começando pela Season 10 — Ebontharn.

## Objetivo

Responder perguntas de jogadores usando RAG, sempre mostrando:

- temporada e patch considerados;
- fontes consultadas;
- data da informação, quando disponível;
- aviso quando não houver evidência recente suficiente.

## Estado atual

A primeira versão implementa o contrato `GameDocument` e um coletor da notícia oficial da Steam sobre a Season 10.

Fonte inicial: [Hero Siege — Ebontharn and Season 10](https://store.steampowered.com/news/app/269210/view/461208205952813643)

Ainda **não** existe bot, banco vetorial ou agente autônomo. Eles entrarão depois que a coleta e a normalização estiverem confiáveis.

## Executar

```bash
uv venv
uv pip install -e ".[dev]"
uv run pytest
uv run python collect_season.py
```

O coletor salva o documento em:

```text
data/raw/hero-siege-season-10-steam.json
```

## Roadmap

- [x] Contrato normalizado para documentos
- [x] Coletor da fonte oficial inicial
- [x] Persistência local em JSON
- [ ] Coletor de patch notes
- [ ] PostgreSQL + pgvector
- [ ] Busca híbrida por texto, temporada e categoria
- [ ] RAG com citações
- [ ] Bot no Discord
- [ ] Avaliação com perguntas reais do grupo

## Regra de coleta

O projeto usa fontes públicas e respeita limites e termos de uso. Não tenta contornar login, CAPTCHA, bloqueios ou mecanismos anti-bot.
