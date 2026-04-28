# Changelog

## 1.1.2 — 28/04/2026

### Corrigido

- Adicionado bootstrap operacional de runtime Python local em `workspace/.venv` para evitar falha por PEP 668 / `externally-managed-environment`.
- Adicionado `dependency_manager.py` com `--runtime-status`, `--no-bootstrap` e preparação automática do `requirements.txt` no primeiro uso real.
- Adicionado `requests_compat.py` como fallback HTTP stdlib quando `requests`, `pip` ou `ensurepip` não estiverem disponíveis no container.
- `registry.py` passou a ser importado de forma lazy pelo executor, evitando crash antes do bootstrap quando dependências externas faltam.
- `first-run` agora inclui status do runtime/dependências no payload JSON.

### Validação

- `python3 -m compileall -q workspace`
- `python3 run.py --runtime-status`
- `python3 run.py --first-run --format json | python3 -m json.tool`
- `python3 run.py --no-bootstrap --wallet 0x0000000000000000000000000000000000000000 --network base --format json | python3 -m json.tool`
- `python3 run.py --no-bootstrap --mode daily --format pretty`

## 1.1.1 — 28/04/2026

### Corrigido

- Fallback Ethereum: quando Ethplorer falha com 502, a skill cai para RPC público + eth.blockscout.com.
- Fallbacks de RPC por rede para reduzir impacto de 429 em Base, Arbitrum, Optimism, Polygon, BNB e Avalanche.
- Output cron/manual sem markdown excessivo, alinhado ao padrão com emojis e linhas por ativo.
- Posições formatadas sem duplicar o símbolo do ativo.
- Avisos técnicos de coleta não poluem mais o output pretty por padrão; use `--show-warnings` para stderr técnico.

## 1.1.0 — 28/04/2026

### Adicionado

- Saída manual e cron unificada no mesmo formato textual.
- Filtragem/auditoria de tokens suspeitos, dust, links, claims e ativos sem preço confiável.
- Hyperliquid com posições, ordens abertas, PnL não realizado, PnL por período, funding e spot filtering.
- Solana SPL com metadata/preço via Jupiter Lite/CoinGecko.
- Solana staking nativo best-effort via RPC público.
- Base/Arbitrum ERC-20 com fallback Dexscreener para preço/liquidez.
- Aave V3 0-key via contratos públicos.
- Compound V3 0-key via contratos Comet públicos.
- Uniswap V3 LP 0-key com detecção de NFTs/positions, sem somar valuation ainda.
- DeBank opcional/premium via `DEBANK_ACCESS_KEY` ou `DEBANK_API_KEY`.
- Documentação OpenClaw/MQC reforçando 0 API keys obrigatórias.

### Segurança

- Exemplos trocados para templates seguros sem wallets reais/sensíveis.
- Segredos continuam fora do Git e devem vir de env/secret manager.
- Ativos sem valuation confiável não entram no total principal.

### Limitações Conhecidas

- Valuation exata de Uniswap V3 LP ainda não entra no total.
- Solana DeFi indexado ainda depende de provider confiável.
- Cobertura EVM varia conforme RPC/Blockscout/Dexscreener disponíveis por rede.

## 1.0.0 — 27/04/2026

- Base inicial da skill com estrutura MQC, executor Python e adaptadores EVM, Solana e Hyperliquid.
