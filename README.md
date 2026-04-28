# multichain-wallet-portfolio

> Skill MQC/OpenClaw para consolidar o portfolio de uma wallet em EVM, Solana e Hyperliquid com saída textual executiva em USD, variação 24h quando disponível e cobertura explícita.

## Visão Geral

A skill roda em modo **somente leitura**. Ela não assina transações, não conecta wallet, não move fundos e não pede seed/private key.

Objetivo principal: entregar um relatório limpo, pronto para uso manual ou cron, com dados confiáveis e sem poluir o resumo com spam/dust/scam tokens.

## O Que Faz

- Consolida **1 wallet por execução**.
- Suporta **EVM + Solana + Hyperliquid**.
- Aceita rede explícita e tenta inferir quando possível.
- Prioriza valores em **USD** quando houver preço confiável.
- Usa o mesmo formato final para análise manual e cron diário.
- Filtra tokens suspeitos, claims, links, airdrops/scams, ativos sem preço confiável e valores irrelevantes.
- Mantém auditoria raw para itens ocultados quando usado em JSON.
- Traz insights curtos e ações sugeridas apenas quando houver motivo claro.

## Cobertura

### EVM

Fontes públicas/0-key:

- saldo nativo via RPC público
- ERC-20 via Blockscout público quando disponível
- preço/liquidez via Dexscreener, CoinGecko e DefiLlama quando disponíveis
- Aave V3 via contratos públicos
- Compound V3 via contratos Comet públicos
- Uniswap V3 LP com detecção de NFTs de posição via Blockscout + `positions(tokenId)`

Redes mapeadas incluem Ethereum, Base, Arbitrum, Optimism, Polygon, BNB/BSC e Avalanche, com cobertura variando por fonte pública disponível.

### Solana

- SOL
- SPL tokens com metadata/preço via Jupiter Lite e fallback CoinGecko quando disponível
- staking nativo SOL best-effort via RPC público
- DeFi Solana indexado ainda depende de provider confiável; a skill não inventa posições

### Hyperliquid

- equity
- spot confiável
- posições abertas
- ordens abertas
- mark price
- PnL não realizado
- PnL por períodos quando inferível por endpoints públicos
- funding agregado quando disponível

## DeFi e Staking

### 0 API Keys Obrigatórias

O fluxo principal foi desenhado para funcionar com **0 API keys obrigatórias**.

| Área | Status | Fonte |
|---|---:|---|
| Aave V3 | ativo | contratos públicos + RPC |
| Compound V3 | ativo | contratos Comet + RPC |
| Uniswap V3 LP | detecção ativa | Blockscout NFT + Position Manager |
| Solana staking | best-effort | RPC público |
| DeBank | opcional | `DEBANK_ACCESS_KEY` ou `DEBANK_API_KEY` |

### Limite Intencional do Uniswap V3 LP

A skill detecta NFTs de liquidez Uniswap V3 e decodifica a posição, mas **não soma valuation da liquidez ao total** enquanto o cálculo exato por pool, tick, preço atual e liquidez não estiver implementado. Isso evita relatório com número falso.

## Providers Opcionais

DeBank Pro pode ser usado como fonte extra/premium de DeFi EVM:

```bash
export DEBANK_ACCESS_KEY="..."
# ou
export DEBANK_API_KEY="..."
```

Regras:

- não é obrigatório;
- não deve ser salvo no Git;
- deve ficar em env/secret manager do runtime MQC;
- se ausente, o fluxo principal continua 0-key.

## Runtime e Dependências

A skill usa Python 3 e `requests>=2.31.0` quando disponível.

Para ambientes PEP 668 / `externally-managed-environment`, o executor agora prepara automaticamente um runtime local em `workspace/.venv` no primeiro uso real e instala `workspace/requirements.txt` nesse venv.

Se o container estiver minimalista e não tiver `ensurepip`/`pip`, a skill não quebra por causa disso: ela segue com um fallback HTTP baseado na stdlib para cobrir as chamadas públicas usadas pelos adapters.

Comandos úteis:

```bash
cd workspace
python3 run.py --runtime-status
python3 run.py --first-run --format json
python3 run.py --no-bootstrap --help
```

## Uso Local

```bash
cd workspace
python3 run.py --help
python3 run.py --first-run --format json
python3 run.py --wallet 0x0000000000000000000000000000000000000000 --network base --format pretty
python3 run.py --wallet exemplo.sol --network solana --format pretty
python3 run.py --wallet 0x0000000000000000000000000000000000000000 --network hyperliquid --format json
```

Modo diário com arquivo local fora do Git:

```bash
python3 run.py --mode daily --wallets-file /caminho/seguro/wallets.json --format pretty
```

Modelo seguro:

```json
{
  "wallets": {
    "evm": "",
    "ethereum": "",
    "base": "",
    "arbitrum": "",
    "optimism": "",
    "polygon": "",
    "bnb": "",
    "solana": "",
    "hyperliquid": ""
  }
}
```

## Formato de Saída

Formato textual unificado:

```text
💼 Portfólio — DD/MM

💰 Total estimado: $VALOR
📈 Variação total 24h: parcial
⚠️ Cobertura: média

◈ Ethereum
📊 ATIVO — DD/MM | $VALOR | 24h: +/-X%
• QUANTIDADE ATIVO

🧠 Insights
- insight objetivo

⚠️ Cobertura por rede
- Rede: fontes e limites

📌 Ações sugeridas
- ação objetiva
```

## Estrutura

```text
multichain-wallet-portfolio/
├── SKILL.md
├── skill.json
├── README.md
├── LICENSE
├── assets/
├── resources/
└── workspace/
    ├── run.py
    ├── dependency_manager.py
    ├── normalizer.py
    ├── registry.py
    ├── requests_compat.py
    ├── token_filters.py
    ├── adapters/
    │   ├── base.py
    │   ├── evm.py
    │   ├── solana.py
    │   └── hyperliquid.py
    └── examples/
```

## Validação

```bash
python3 -m json.tool skill.json >/dev/null
python3 -m compileall -q workspace
(cd workspace && python3 run.py --help)
(cd workspace && python3 run.py --runtime-status)
(cd workspace && python3 run.py --first-run --format json | python3 -m json.tool >/dev/null)
(cd workspace && python3 run.py --mode daily --format pretty)
```

## Segurança

- Nunca coloque wallets reais privadas em `workspace/examples/`.
- Nunca commite `.env`, chaves, tokens, cookies, seeds ou private keys.
- Use env/secret manager para credenciais opcionais.
- A skill deve preferir dados públicos e declarar cobertura parcial quando a fonte não for suficiente.

## Changelog

Consulte [`CHANGELOG.md`](./CHANGELOG.md).

## Licença

Proprietary — natanaelhx
