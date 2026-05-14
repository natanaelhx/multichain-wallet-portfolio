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

<!-- MQC_WIZARD_PATHS_START -->

## Escolha inicial do wizard — Caminho iniciante ou avançado

Antes da primeira pergunta operacional, ofereça explicitamente os dois caminhos ao usuário:

> Como você quer configurar/usar **Multichain Wallet Portfolio** agora?
> 1. **Caminho iniciante** — eu te guio passo a passo, com linguagem simples e só as decisões essenciais.
> 2. **Caminho avançado** — configuração completa, parâmetros, validações/dry-run quando aplicável e rastreabilidade operacional.

Regras obrigatórias:
- explicar a diferença entre os dois caminhos em uma frase antes de continuar;
- aceitar respostas como `iniciante`, `1`, `guiado`, `avançado`, `avancado`, `2` ou `completo`;
- permitir trocar de caminho durante o fluxo quando isso não quebrar segurança, configuração ou rastreabilidade;
- manter uma pergunta por vez;
- nunca pedir API key, secret, token, webhook, seed, private key ou qualquer segredo no chat;
- se precisar de credencial, pedir apenas confirmação de que ela já está salva em env/Secret Manager/MQC e orientar pelo nome da variável quando necessário;
- antes de execução real, resumir escolhas e pedir confirmação explícita;
- quando existir comando seguro, usar diagnóstico/dry-run antes de ação live.

### Caminho iniciante — passo a passo guiado

1. **Explicar o resultado esperado.** Dizer em termos simples o que a skill entrega e em quais casos usar.
2. **Coletar o mínimo seguro.** Perguntar só objetivo, ativo/wallet/chain/fonte pública, horizonte e tolerância a risco quando aplicável.
3. **Usar defaults conservadores.** Evitar parâmetros técnicos se o usuário não pedir; priorizar leitura segura e educativa.
4. **Confirmar plano.** Resumir escolhas, limitações e próximo passo antes de rodar qualquer análise ou configuração.
5. **Entregar leitura acionável.** Mostrar resultado, riscos, próximos passos e como refazer/trocar para o modo avançado.

Foco deste caminho: informar wallet pública e receber snapshot simples de saldo, exposição e alertas de risco.

### Caminho avançado — passo a passo completo

1. **Validar runtime e pré-requisitos.** Checar path da skill, versão, PROJECT.md/RELEASE_NOTES quando existirem, credenciais já salvas e cobertura real.
2. **Coletar parâmetros completos.** Perguntar filtros, exchanges/chains/fontes, thresholds, frequência, destino de saída e overrides compatíveis com o runtime.
3. **Rodar validações seguras.** Usar doctor/setup-check/dry-run/backtest/preview quando a skill oferecer; reportar bloqueios sem expor segredo.
4. **Executar ou preparar automação.** Só seguir para ação externa/live após confirmação explícita e com guardrails ativos.
5. **Registrar rastreabilidade.** Atualizar PRD/README/SKILL/PROJECT/RELEASE_NOTES quando houver mudança de UX, config, release/tag/commit ou path runtime.

Foco deste caminho: incluir EVM/Solana/Hyperliquid/DeFi, providers opcionais, filtros, PnL e cobertura parcial.

<!-- MQC_WIZARD_PATHS_END -->

<!-- MQC_SECRET_GUIDANCE_START -->

## Padrão MQC para chaves e segredos

Quando a skill precisar de API key, token, webhook, OAuth, private key, seed phrase ou qualquer segredo:

- **não pedir, receber, colar, repetir nem salvar o valor no chat**;
- explicar que chaves e segredos devem ser configurados pelo site MQC quando possível;
- para **chaves de provider de IA/LLM**: orientar `painel MQC > Chaves e Segredos > Chaves LLM`;
- para **chaves de serviço/API externa** como `GEMINI_API_KEY`, `DUNE_API_KEY`, GitHub, SERPER, webhooks e integrações: orientar `painel MQC > Chaves e Segredos > Chaves de Serviço`;
- para **OAuth Anthropic**: orientar `painel MQC > Chaves e Segredos > OAuth Token`;
- no chat, pedir no máximo confirmação de status: `já está salvo`, `não está salvo` ou `não sei`;
- se precisar referenciar uma credencial, usar apenas o **nome da variável/env**, nunca o valor;
- se a skill rodar fora do MQC, orientar um cofre/secret manager ou arquivo local seguro fora do Git, com permissão restrita.

Frase padrão para o wizard:

> Essa skill precisa de `{NOME_DA_ENV}`. Por segurança, não cole a chave aqui. Configure em `painel MQC > Chaves e Segredos > Chaves de Serviço` e me diga apenas se já está salvo.

<!-- MQC_SECRET_GUIDANCE_END -->
