# PROJECT.md — multichain-wallet-portfolio

## Produção

- Repo org: `QuickClaw-Skills/skill-multichain-wallet-portfolio`
- Runtime MQC: `~/.openclaw/skills/multichain-wallet-portfolio`
- Última release aprovada: `v1.1.4`
- Versão: `1.1.4`
- Commit: `tag:v1.1.4`
- Data: 2026-05-13

## Notas operacionais

- Skill somente leitura para EVM, Solana e Hyperliquid.
- Fluxo principal 0-key; DeBank é provider opcional via `DEBANK_ACCESS_KEY` ou `DEBANK_API_KEY` no ambiente/secret manager.
- Nunca salvar wallets sensíveis, seed, private key, API keys ou arquivos `.env` no Git.
- Wizard chat-first: `references/onboarding-questionario.md` e `workspace/first_run_setup.py --json`.
- Executor operacional preservado: `workspace/run.py`.

## Atualização local — v1.1.5 (2026-05-13)

- Wizard atualizado para escolha inicial entre **Caminho iniciante** e **Caminho avançado**.
- Passo a passo dos dois caminhos registrado em `references/onboarding-questionario.md`.
- Versão local em `skill.json`: `1.1.5`.
- Release/tag/commit oficial ainda pendente para produção.
- Payload first-run atualizado para iniciar por `wizard_path` e permitir escolha entre caminho iniciante/avançado.
- Guardrail MQC de chaves/segredos aplicado: orientar pelo dashboard da plataforma e nunca pedir valores no chat.
- Versão local `1.1.6`: payload do wizard inclui `credential_guidance` estruturado para orientar usuário pelo painel MQC em Chaves e Segredos, sem depender da LLM.
