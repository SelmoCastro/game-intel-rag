# Contribuindo

## Fluxo obrigatório

1. Atualize `master`:

```bash
git switch master
git pull --ff-only origin master
```

2. Crie uma branch descritiva:

```bash
git switch -c feat/nome-da-feature
```

Prefixos aceitos:

- `feat/` — funcionalidade;
- `fix/` — correção;
- `refactor/` — refatoração;
- `test/` — testes;
- `docs/` — documentação;
- `ci/` — automação;
- `chore/` — manutenção.

3. Rode a validação antes do commit:

```bash
uv sync --extra dev
uv run pytest
```

4. Faça commits no padrão Conventional Commits:

```text
type(scope): descrição curta no imperativo
```

Exemplos:

```text
feat(rag): add pgvector similarity search
fix(collector): handle empty Steam RSS description
test(store): cover duplicate document ingestion
chore(ci): require pytest on pull requests
```

5. Envie a branch e abra um PR para `master`:

```bash
git push -u origin HEAD
gh pr create --base master
```

## Regras

- Não fazer push direto em `master`.
- Não usar credenciais em código, `.env.example` ou commits.
- Todo PR precisa passar pelo check `Lint & Type Check`.
- O PR deve explicar mudança, risco e validação executada.
- Commits devem ser pequenos e focados.
