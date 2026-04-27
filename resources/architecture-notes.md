# Architecture Notes

## Direção da v1

- 1 wallet por execução
- foco em USD
- variação 24h quando disponível
- saída textual + JSON estruturado interno
- sem key por padrão
- provider opcional preparado, mas não integrado ainda

## Adapters

- `evm.py` → catálogo de redes EVM por configuração
- `solana.py` → SOL, SPL e staking/DeFi quando a fonte suportar
- `hyperliquid.py` → equity, posições e ordens abertas

## Honestidade operacional

A v1 deve preferir retorno parcial transparente a inventar cobertura.

## Expansões futuras

- provider opcional para preços/portfolio enriquecido
- NFTs fora do bloco principal
- CEX tradicional separado da trilha onchain
