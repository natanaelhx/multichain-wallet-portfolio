# multichain-wallet-portfolio

> Skill MQC operacional para consolidar portfolio de uma wallet em EVM, Solana e Hyperliquid com saída executiva em USD, variação 24h e cobertura explícita.

## O que faz

- consolida **1 wallet por execução**
- cobre **EVM + Solana + Hyperliquid**
- tenta detectar a rede e aceita rede explícita
- retorna **resumo executivo + blocos detalhados**
- prioriza **USD** quando houver preço
- tenta calcular **variação 24h** por carteira, ativo e posição quando houver suporte
- destaca **stablecoins**, **concentração**, **categorias principais** e **diversificação simples**
- traz **insights curtos** e **ações sugeridas** só quando houver motivo claro

## Status da v1

Esta v1 nasce como **base operacional honesta**:
- com executor real em Python
- com adaptadores separados
- com fallback entre fontes públicas
- sem prometer cobertura mágica onde ainda não houver fonte suficiente

## Cobertura alvo da v1

### EVM
- redes EVM por **catálogo configurável**
- começa com principais redes públicas
- expansão fácil por configuração

### Solana
- SOL
- SPL tokens
- staking quando visível
- posições DeFi quando a fonte permitir

### Hyperliquid
- equity
- posições
- ordens abertas

## Estrutura

```text
repo/
├── SKILL.md
├── skill.json
├── README.md
├── LICENSE
├── PRD.html
├── multichain-wallet-portfolio-prd.html
├── .gitignore
├── assets/
│   └── myquickclaw-brand.jpg
├── resources/
│   └── architecture-notes.md
└── workspace/
    ├── run.py
    ├── normalizer.py
    ├── registry.py
    ├── first_run_setup.py
    ├── requirements.txt
    ├── adapters/
    │   ├── base.py
    │   ├── evm.py
    │   ├── solana.py
    │   └── hyperliquid.py
    └── examples/
```

## Uso local

```bash
cd workspace
python3 run.py --wallet vitalik.eth --network ethereum --format pretty
python3 run.py --wallet 0x000000000000000000000000000000000000dead --network base --format json
python3 run.py --wallet somewallet.sol --network solana --format pretty
python3 run.py --wallet 0xabc123 --network hyperliquid --format json
```

## Observações importantes

- a v1 é **somente leitura**
- não assina, não move fundos, não conecta wallet
- sem API key por padrão
- providers opcionais podem ser adicionados depois sem quebrar a arquitetura
- CEX tradicional fica fora desta v1

## Changelog

| Versão | Data | Mudança |
|--------|------|---------|
| 1.0.0 | 27/04/2026 | Base inicial da skill `multichain-wallet-portfolio` com estrutura MQC completa, PRD inicial e executor Python com adaptadores EVM, Solana e Hyperliquid |

## Licença

Proprietary — natanaelhx
