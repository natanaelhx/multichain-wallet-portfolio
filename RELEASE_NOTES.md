## v1.1.3 — 2026-05-13

> Bump: PATCH
> Compatibilidade: sem quebra. Padroniza wizard chat-first no padrão Skill Builder mantendo executor e coleta existentes.

### Added
- `references/onboarding-questionario.md` com fluxo curto de onboarding.
- `workspace/first_run_setup.py --json` com payload estruturado para MQC/OpenClaw.
- `skill.json.metadata.wizard` com entrypoints, referência e guardrails.
- `PROJECT.md` com release/tag/commit da skill.

### Changed
- `workspace/run.py --first-run --format json` preservado, agora alimentado por payload Skill Builder mais completo.
- `SKILL.md` documenta wizard, entrypoints e guardrails de segurança.
- PRD HTML reforça slash path oficial e intenções naturais.

### Security
- Wizard não pede seed phrase, private key, mnemonic, token, API key, webhook ou segredo no chat.
- Skill permanece somente leitura: não conecta wallet, não assina transações e não move fundos.
- DeBank continua provider opcional via ambiente/secret manager, nunca obrigatório.

### Validation
- [x] `python3 workspace/first_run_setup.py --json`
- [x] `python3 workspace/run.py --first-run --format json --no-bootstrap`
- [x] `python3 workspace/run.py --runtime-status`
- [x] `python3 -m py_compile workspace/*.py workspace/adapters/*.py`

## v1.1.2 — 2026-04-28

### Corrigido

- Adicionado bootstrap operacional de runtime Python local em `workspace/.venv` para evitar falha por PEP 668 / `externally-managed-environment`.
- Adicionado `dependency_manager.py` com `--runtime-status`, `--no-bootstrap` e preparação automática do `requirements.txt` no primeiro uso real.
- Adicionado `requests_compat.py` como fallback HTTP stdlib quando `requests`, `pip` ou `ensurepip` não estiverem disponíveis no container.
- `registry.py` passou a ser importado de forma lazy pelo executor, evitando crash antes do bootstrap quando dependências externas faltam.
- `first-run` agora inclui status do runtime/dependências no payload JSON.
