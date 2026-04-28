---
name: multichain-wallet-portfolio
description: >
  Consolida portfolio de uma wallet por execução em EVM, Solana e Hyperliquid.
  Use quando o usuário pedir saldo, snapshot, tokens, posições DeFi/staking,
  ordens abertas, PnL, exposição, stablecoins, concentração ou resumo diário de
  carteira. Opera em modo somente leitura, prioriza fontes públicas/0-key e
  sinaliza cobertura parcial sem inventar dados. Keywords: wallet portfolio,
  multichain, evm, solana, hyperliquid, defi, staking, aave, compound, uniswap,
  balances, holdings, positions, pnl, exposure, 24h change
---

# Multichain Wallet Portfolio

Skill MQC/OpenClaw para gerar snapshot textual de portfolio de **uma wallet por execução** em **EVM, Solana e Hyperliquid**.

A skill é **somente leitura**: não assina transações, não conecta wallet, não move fundos e não executa operações financeiras.

## Quando Usar

Use quando o usuário pedir:

- saldo ou resumo de uma wallet
- portfolio multi-chain em USD
- tokens ERC-20/SPL com valor confiável
- staking Solana nativo
- posições DeFi EVM, especialmente Aave V3, Compound V3 e Uniswap V3 LP
- equity, posições, ordens abertas ou PnL em Hyperliquid
- relatório manual ou saída pronta para cron diário
- exposição, stablecoins, concentração, variação 24h ou insights curtos

## Como Funciona

1. Identifica a wallet e a rede.
2. Se a rede não vier explícita, tenta inferir.
3. Quando houver ambiguidade, pergunta uma coisa por vez.
4. Coleta dados por adaptadores:
   - EVM: Ethereum, Base, Arbitrum, Optimism, Polygon, BNB/BSC, Avalanche e redes compatíveis mapeadas.
   - Solana: SOL, SPL tokens e staking nativo best-effort.
   - Hyperliquid: equity, posições, ordens abertas e PnL via API pública.
5. Filtra spam/dust/scam tokens do output principal.
6. Mantém ativos ocultados em auditoria raw quando o executor retornar JSON.
7. Renderiza relatório textual único, usado tanto no fluxo manual quanto em cron.

## Cobertura 0-Key

A skill deve funcionar sem API key obrigatória.

Fontes públicas usadas quando disponíveis:

- RPC público EVM
- RPC público Solana
- Hyperliquid API pública
- Blockscout público
- Dexscreener público
- CoinGecko/DefiLlama públicos
- Jupiter Lite API
- contratos públicos Aave V3
- contratos Comet Compound V3
- Uniswap V3 NonfungiblePositionManager + NFTs via Blockscout

## Providers Opcionais

- `DEBANK_ACCESS_KEY` ou `DEBANK_API_KEY` ativa DeBank Pro como fonte extra/premium de DeFi EVM.
- A skill nunca deve exigir DeBank para o fluxo principal.
- Se a chave não existir, não chame DeBank e não invente posições.
- Nunca salve chaves, wallets reais privadas ou arquivos `.env` no Git.

## Regras de Segurança e Qualidade

- **SEMPRE** explicar que é leitura de dados, não execução de transações.
- **SEMPRE** responder em PT-BR.
- **SEMPRE** sinalizar fontes, cobertura e lacunas materiais.
- **SEMPRE** ocultar do output principal tokens suspeitos, links/claims/airdrops/scams, ativos sem preço confiável ou valor abaixo do limite operacional.
- **SEMPRE** preservar dados filtrados no raw audit quando o modo JSON for usado.
- **NUNCA** inventar preço, PnL, valuation DeFi ou histórico.
- **NUNCA** somar Uniswap V3 LP ao total enquanto a valuation exata por pool/tick/liquidez não estiver implementada.
- **NUNCA** misturar CEX tradicional com cobertura onchain; Hyperliquid tem trilha própria.
- **NUNCA** pedir ou registrar seed phrase, private key, mnemonic ou segredo.

## Perguntas ao Usuário

Quando faltar contexto, siga o onboarding MQC:

1. explique rapidamente o fluxo completo;
2. faça **uma pergunta por vez**;
3. use emoji na pergunta;
4. permita uma ou mais opções quando oferecer escolhas.

Exemplo:

> Vou ler a wallet em modo somente leitura, consolidar redes suportadas, filtrar spam e devolver um relatório em USD com cobertura explícita. 🔎 Qual wallet você quer analisar?

## Formato de Resposta

A saída textual principal deve seguir o padrão cron/manual unificado:

```text
# 💼 Portfólio — DD/MM

💰 Total estimado: $VALOR
📈 Variação total 24h: parcial
⚠️ Cobertura: baixa/média/alta

### ◈ Ethereum
📊 ATIVO — DD/MM | $VALOR | 24h: +/-X%
• QUANTIDADE ATIVO

## 🧠 Insights
- insight curto

## ⚠️ Cobertura por rede
- Rede: fonte e limites

## 📌 Ações sugeridas
- ação objetiva, se houver
```

## Exemplos

### Snapshot EVM

**Usuário:** `analisa 0xabc... na Base`

**Resposta esperada:** relatório textual com saldo nativo, tokens confiáveis, DeFi 0-key detectado, cobertura e limites.

### Cron diário

**Usuário:** `gera resumo diário das minhas wallets`

**Resposta esperada:** mesma estrutura do modo manual, sem blocos extras incompatíveis.

### DeFi sem fonte confiável

**Usuário:** `mostra minhas posições DeFi Solana`

**Resposta esperada:** retornar staking nativo quando disponível e explicar que DeFi Solana indexado exige provider confiável; não inventar posições.
