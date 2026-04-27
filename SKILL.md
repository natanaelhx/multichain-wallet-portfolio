---
name: multichain-wallet-portfolio
description: >
  Consolida portfolio de uma wallet por execução em múltiplas redes. Ative esta
  skill quando o usuário pedir snapshot de wallet, saldo total, tokens, posições,
  ordens abertas, exposição, stablecoins, concentração, variação de 24h ou visão
  consolidada em EVM, Solana ou Hyperliquid. A skill tenta detectar a rede,
  aceita rede explícita, responde em PT-BR com resumo executivo e blocos
  detalhados, e retorna cobertura/confiança de forma transparente. Use fontes
  públicas por padrão e providers opcionais só quando existirem. Keywords:
  wallet portfolio, multichain, evm, solana, hyperliquid, holdings, balances,
  tokens, positions, 24h change, exposure, stablecoins
---

# Multichain Wallet Portfolio

Skill operacional para leitura de **portfolio por wallet** em **EVM, Solana e Hyperliquid**.

## Quando usar

- O usuário quer ver **saldo**, **tokens** ou **posições** de uma wallet
- O usuário quer um **snapshot multi-chain** com foco em **USD**
- O usuário quer **variação das últimas 24h** quando houver dado disponível
- O usuário quer ver **concentração**, **stablecoins**, **categorias** e **insights curtos**
- O usuário quer checar **ordens abertas e posições** em **Hyperliquid**
- O usuário quer analisar uma wallet de **Ethereum/EVM**, **Solana** ou **Hyperliquid**

## Workflow obrigatório

1. **Explique rapidamente o que a skill faz** antes da primeira pergunta: leitura de portfolio, sem assinar transação, sem mover fundos e em modo somente leitura.
2. **Explique o fluxo completo**: identificar wallet/rede, coletar dados por adaptadores, consolidar o resultado, sinalizar cobertura e devolver resumo objetivo.
3. **Faça uma pergunta por vez** quando faltar contexto.
4. **Explique o motivo da pergunta** antes de fazê-la.
5. **Use emoji nas perguntas**.
6. Se a rede não vier explícita:
   - tente detectar automaticamente
   - se houver ambiguidade material, pergunte ao usuário
7. Se alguma fonte só permitir **cobertura parcial**, devolva o que conseguiu com transparência.
8. Se houver alias/domínio resolvível, tente resolver primeiro; se falhar, avise claramente.

## Regras de operação

- **1 wallet por execução** na v1
- Priorizar **USD** na resposta textual
- Tentar obter **variação 24h** para:
  - carteira total
  - ativos
  - posições
  quando a fonte permitir
- Tentar múltiplas fontes antes de assumir retorno parcial
- Expor sempre:
  - fonte usada
  - cobertura obtida
  - limites/lacunas
- **NFTs são opcionais** e ficam fora do resumo principal
- **CEX tradicional fica fora da v1**; Hyperliquid tem trilha própria
- Não inventar preço, posição, PnL ou histórico quando a fonte não suportar

## Saída esperada

- **Resumo executivo** com emoji
- **Blocos detalhados** por categoria
- **Valores em USD** quando disponíveis
- **Variação 24h** quando disponível
- **Score simples de diversificação**: baixa / média / alta
- **Insights curtos e conservadores**
- **Ações sugeridas** só quando houver motivo claro
- **Cobertura parcial no topo** apenas se impactar materialmente o resultado

## Trilhas da v1

### EVM
- Catálogo de redes aberto por configuração
- Começa com redes EVM principais, mas sem lista rígida no prompt
- Autodetecta quando possível; pergunta se ficar ambíguo

### Solana
- SOL
- SPL tokens
- staking quando visível
- posições DeFi quando disponíveis

### Hyperliquid
- equity / saldo
- posições
- ordens abertas

## Formato de resposta

- **Idioma:** PT-BR
- **Tom:** direto e técnico
- **Estrutura padrão:**
  - Resumo executivo
  - Cobertura / confiança
  - Saldos e ativos
  - Posições
  - Insights
  - Próximo passo sugerido (se houver)

## Regras finais

- **SEMPRE** dizer que é leitura de dados, não execução de transações
- **SEMPRE** fazer uma pergunta por vez quando faltar contexto
- **SEMPRE** usar emoji nas perguntas
- **SEMPRE** sinalizar cobertura e lacunas reais
- **NUNCA** afirmar “todas as redes” sem base operacional real
- **NUNCA** inventar preço em USD se a fonte não trouxer dado confiável
- **NUNCA** misturar dados onchain com exchange/CEX na v1 como se fossem a mesma cobertura
