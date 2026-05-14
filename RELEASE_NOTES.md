## v1.1.6 — 2026-05-13

> Bump: PATCH
> Compatibilidade: sem quebra. Torna a orientação de credenciais determinística no payload do wizard.

### Added
- `credential_guidance` estruturado no payload `first_run_setup.py --json`, com texto pronto para usuário e caminhos do painel MQC em **Chaves e Segredos**.

### Changed
- Wizard não depende mais da LLM para explicar onde configurar chaves/segredos; a orientação vem pronta no payload.

### Security
- Reforçado: nunca pedir API key, token, webhook, OAuth, private key, seed ou secret value no chat.

### Validation
- [x] `first_run_setup.py --json` retorna `next_question.field = wizard_path`.
- [x] `credential_guidance.must_show_to_user = true`.

## Security guidance — 2026-05-13

### Security
- Padronizada orientação MQC para chaves e segredos: nunca pedir valores no chat; orientar Chaves LLM, Chaves de Serviço ou OAuth Token conforme o tipo de credencial.

## v1.1.5 — 2026-05-13

> Bump: PATCH
> Compatibilidade: sem quebra. Atualiza wizard para o padrão MQC por caminhos.

### Added
- Escolha inicial no wizard entre **Caminho iniciante** e **Caminho avançado**.
- Passo a passo documentado para os dois caminhos em `references/onboarding-questionario.md`.

### Changed
- `SKILL.md` e `README.md` passam a apontar explicitamente para o wizard por caminhos.
- `first_run_setup.py` agora emite `wizard_path` como primeira pergunta, `wizard_paths` no payload e `question_flow` iniciado pela escolha de caminho.

### Security
- Mantido guardrail de nunca pedir segredos no chat; credenciais devem estar em env/Secret Manager/MQC.

### Validation
- [ ] Validar comando mínimo/runtime específico da skill antes da release oficial.

## v1.1.4 — 2026-05-13

> Bump: PATCH
> Compatibilidade: sem quebra. Publica a skill no repositório canônico da org QuickClaw-Skills.

### Changed
- Repo canônico alinhado para `QuickClaw-Skills/skill-multichain-wallet-portfolio`.
- `skill.json.homepage`, `PROJECT.md` e `skill.json.metadata.last_release` atualizados para `v1.1.4`.

### Validation
- [x] `multichain_wizard_ok`

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
