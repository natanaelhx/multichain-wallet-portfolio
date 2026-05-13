# Onboarding — multichain-wallet-portfolio

## Objetivo

Conduzir o primeiro uso da skill **multichain-wallet-portfolio** em modo chat-first, uma pergunta por vez, sem bloquear runtime não interativo e sem solicitar segredos.

A skill é **somente leitura**: consulta dados públicos/0-key e providers opcionais, não conecta wallet, não assina transações, não move fundos e não executa operação financeira.

## Regras obrigatórias

- Responder em PT-BR.
- Explicar o fluxo antes da primeira pergunta.
- Fazer **uma pergunta por vez**.
- Não pedir seed phrase, private key, mnemonic, token, API key, webhook ou qualquer segredo no chat.
- Não pedir a chave DeBank; no máximo confirmar se um provider opcional já está configurado no ambiente/secret manager.
- Não inventar saldo, preço, PnL, posição DeFi, staking ou valuation ausente.
- Sinalizar cobertura parcial quando fonte pública/provider não cobrir uma rede.
- Manter o fluxo principal 0-key e somente leitura.

## Fluxo curto recomendado

### 1. Wallet

**Motivo:** sem wallet não há alvo para leitura.

**Pergunta:**

> Vou ler a carteira em modo somente leitura, consolidar redes suportadas e te devolver um resumo com cobertura explícita. 🔎 Qual wallet você quer analisar?

### 2. Rede / escopo

**Motivo:** evita misturar cobertura e reduz chamadas desnecessárias.

**Pergunta quando a rede não estiver clara:**

> 🌐 Você quer que eu autodetecte a rede ou prefere informar uma rede específica? Opções: autodetectar, evm-multichain, ethereum, base, arbitrum, optimism, polygon, bnb, avalanche, solana ou hyperliquid.

### 3. Escopo de saída

**Motivo:** define se a entrega deve ser snapshot simples, DeFi/staking, Hyperliquid ou resumo diário.

**Pergunta:**

> 📊 Qual escopo você quer agora: snapshot, defi-staking, hyperliquid, daily ou completo?

### 4. Formato

**Motivo:** diferencia resposta legível no chat de payload auditável/automação.

**Pergunta:**

> 🧾 Você prefere saída em resumo ou json?

## Confirmação final

Quando houver contexto suficiente:

> Perfeito. Vou consultar `{wallet}` em `{network}` no modo `{scope}`, somente leitura, e entregar em `{output_format}`. Não vou pedir nem usar seed/private key.

## Payload JSON esperado

```json
{
  "ok": true,
  "mode": "chat_first_onboarding",
  "skill": "multichain-wallet-portfolio",
  "reference": "references/onboarding-questionario.md",
  "question_strategy": {
    "one_question_at_a_time": true,
    "never_request_secrets_in_chat": true,
    "read_only": true
  },
  "state": {
    "wallet": null,
    "network": "autodetect",
    "scope": "snapshot",
    "output_format": "summary",
    "questionnaire_completed": false
  },
  "next_question": {
    "field": "wallet",
    "question": "Vou ler a carteira em modo somente leitura... Qual wallet você quer analisar?"
  }
}
```
