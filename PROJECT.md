# PROJECT.md — multichain-wallet-portfolio

## Produção

- Repo: `natanaelhx/multichain-wallet-portfolio`
- Runtime MQC: `~/.openclaw/skills/multichain-wallet-portfolio`
- Última release aprovada: `v1.1.3`
- Versão: `1.1.3`
- Commit: `tag:v1.1.3`
- Data: 2026-05-13

## Notas operacionais

- Skill somente leitura para EVM, Solana e Hyperliquid.
- Fluxo principal 0-key; DeBank é provider opcional via `DEBANK_ACCESS_KEY` ou `DEBANK_API_KEY` no ambiente/secret manager.
- Nunca salvar wallets sensíveis, seed, private key, API keys ou arquivos `.env` no Git.
- Wizard chat-first: `references/onboarding-questionario.md` e `workspace/first_run_setup.py --json`.
- Executor operacional preservado: `workspace/run.py`.
