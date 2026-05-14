#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from typing import Any


CREDENTIAL_GUIDANCE = {
    "must_show_to_user": True,
    "title": "Onde configurar chaves e segredos no MQC",
    "short_explanation": "Por segurança, não envie API keys, tokens, webhooks, OAuth, private keys, seeds ou secrets pelo chat. Configure tudo no painel MQC em Chaves e Segredos e depois me diga apenas se já está salvo.",
    "paths": {
        "llm_provider_keys": "painel MQC > Chaves e Segredos > Chaves LLM",
        "service_api_keys": "painel MQC > Chaves e Segredos > Chaves de Serviço",
        "anthropic_oauth": "painel MQC > Chaves e Segredos > OAuth Token"
    },
    "chat_allowed_answers": ["já está salvo", "não está salvo", "não sei"],
    "never_ask_for": ["API key", "token", "webhook", "OAuth token", "private key", "seed phrase", "secret value"],
    "user_message_template": "Essa skill precisa de {credential_name}. Por segurança, não cole a chave aqui. Configure em painel MQC > Chaves e Segredos > {section} e me diga apenas se já está salvo.",
}

WIZARD_PATH_CHOICE = {
    "field": "wizard_path",
    "reason": "Define o nível de detalhe do wizard antes das perguntas operacionais.",
    "question": "Como você quer seguir: 1) Caminho iniciante — passo a passo guiado e simples; ou 2) Caminho avançado — configuração completa com validações/dry-run quando aplicável?",
    "options": ["iniciante", "avancado"],
    "aliases": {"1": "iniciante", "guiado": "iniciante", "simples": "iniciante", "2": "avancado", "avançado": "avancado", "completo": "avancado"},
    "default": "iniciante",
}

WIZARD_PATHS = {
    "choice_required": True,
    "beginner": {
        "label": "Caminho iniciante",
        "description": "Passo a passo guiado, linguagem simples, defaults seguros e só as decisões essenciais.",
    },
    "advanced": {
        "label": "Caminho avançado",
        "description": "Configuração completa, parâmetros, validações/dry-run quando aplicável e rastreabilidade operacional.",
    },
    "can_switch_when_safe": True,
    "never_request_secrets_in_chat": True,
}

INTRODUCTION = (
    "Esta skill lê uma wallet em modo somente leitura, consolida redes suportadas "
    "e entrega um resumo de portfólio com cobertura explícita. Ela não conecta wallet, "
    "não assina transações, não move fundos e nunca precisa de seed/private key."
)

SUPPORTED_NETWORKS = [
    "autodetect",
    "evm-multichain",
    "ethereum",
    "base",
    "arbitrum",
    "optimism",
    "polygon",
    "bnb",
    "avalanche",
    "solana",
    "hyperliquid",
]

SUPPORTED_SCOPES = ["snapshot", "defi-staking", "hyperliquid", "daily", "complete"]
SUPPORTED_FORMATS = ["summary", "json"]


def explain_workflow() -> list[str]:
    return [
        "Explicar rapidamente que a skill faz leitura de portfolio e nao move fundos.",
        "Pedir primeiro a wallet que sera analisada.",
        "Autodetectar a rede quando possivel e confirmar quando houver ambiguidade.",
        "Coletar dados pelos adapters de EVM, Solana ou Hyperliquid.",
        "Consolidar USD, variacao 24h, concentracao, categorias, cobertura e limites reais.",
        "Entregar resumo executivo e proximos passos sem inventar dados ausentes.",
        "Preparar automaticamente o venv local da skill quando o runtime ainda nao tiver dependencias.",
    ]


def _normalize_network(value: str | None) -> str:
    if not value:
        return "autodetect"
    raw = value.strip().lower().replace("_", "-")
    aliases = {
        "auto": "autodetect",
        "inferir": "autodetect",
        "evm": "evm-multichain",
        "multi-evm": "evm-multichain",
        "bsc": "bnb",
        "binance": "bnb",
        "avax": "avalanche",
        "hyper": "hyperliquid",
        "hl": "hyperliquid",
    }
    return aliases.get(raw, raw if raw in SUPPORTED_NETWORKS else "autodetect")


def _normalize_scope(value: str | None) -> str:
    if not value:
        return "snapshot"
    raw = value.strip().lower().replace("_", "-")
    aliases = {
        "resumo": "snapshot",
        "portfolio": "snapshot",
        "portfólio": "snapshot",
        "defi": "defi-staking",
        "staking": "defi-staking",
        "completo": "complete",
        "all": "complete",
        "cron": "daily",
        "diario": "daily",
        "diário": "daily",
    }
    return aliases.get(raw, raw if raw in SUPPORTED_SCOPES else "snapshot")


def _normalize_format(value: str | None) -> str:
    if not value:
        return "summary"
    raw = value.strip().lower()
    aliases = {"resumo": "summary", "texto": "summary", "pretty": "summary"}
    return aliases.get(raw, raw if raw in SUPPORTED_FORMATS else "summary")


def _question_flow() -> list[dict[str, Any]]:
    return [
        {
            "field": "wallet",
            "reason": "Sem wallet não há alvo para leitura.",
            "question": "Vou ler a carteira em modo somente leitura, consolidar redes suportadas e te devolver um resumo com cobertura explícita. 🔎 Qual wallet você quer analisar?",
            "default": None,
        },
        {
            "field": "network",
            "reason": "Evita misturar cobertura e reduz chamadas desnecessárias.",
            "question": "🌐 Você quer que eu autodetecte a rede ou prefere informar uma rede específica?",
            "options": SUPPORTED_NETWORKS,
            "default": "autodetect",
        },
        {
            "field": "scope",
            "reason": "Define se a entrega deve focar snapshot simples, DeFi/staking, Hyperliquid ou resumo diário.",
            "question": "📊 Qual escopo você quer agora: snapshot, defi-staking, hyperliquid, daily ou completo?",
            "options": SUPPORTED_SCOPES,
            "default": "snapshot",
        },
        {
            "field": "output_format",
            "reason": "Diferencia resposta legível no chat de payload auditável/automação.",
            "question": "🧾 Você prefere saída em resumo ou json?",
            "options": SUPPORTED_FORMATS,
            "default": "summary",
        },
    ]


def _next_question(state: dict[str, Any]) -> dict[str, Any] | None:
    for question in _question_flow():
        field = question["field"]
        if field == "wallet" and not state.get("wallet"):
            return question
        if field == "network" and state.get("network") in {None, ""}:
            return question
        if field == "scope" and not state.get("scope"):
            return question
        if field == "output_format" and not state.get("output_format"):
            return question
    return None


def build_wizard_payload(
    *,
    wallet: str | None = None,
    network: str | None = None,
    scope: str | None = None,
    output_format: str | None = None,
) -> dict[str, Any]:
    state = {
        "wallet": wallet.strip() if isinstance(wallet, str) and wallet.strip() else None,
        "network": _normalize_network(network),
        "scope": _normalize_scope(scope),
        "output_format": _normalize_format(output_format),
        "questionnaire_completed": False,
    }
    state.setdefault("wizard_path", None)
    next_question = _next_question(state)
    state["questionnaire_completed"] = next_question is None

    payload = {
        "ok": True,
        "mode": "chat_first_onboarding",
        "skill": "multichain-wallet-portfolio",
        "introduction": INTRODUCTION,
        "reference": "references/onboarding-questionario.md",
        "credential_guidance": CREDENTIAL_GUIDANCE,
        "workflow": explain_workflow(),
        "required_fields": ["wallet"],
        "optional_fields": ["network", "scope", "output_format"],
        "question_strategy": {
            "one_question_at_a_time": True,
            "use_emoji": True,
            "explain_reason": True,
            "language": "pt-BR",
            "never_request_secrets_in_chat": True,
            "read_only": True,
        },
        "wizard_paths": WIZARD_PATHS,
        "question_flow": [WIZARD_PATH_CHOICE] + _question_flow(),
        "next_question": WIZARD_PATH_CHOICE if next_question is not None else None,
        "state": state,
        "safe_commands": {
            "first_run": "python3 workspace/run.py --first-run --format json",
            "single": "python3 workspace/run.py --wallet 0x... --network base --format pretty",
            "json": "python3 workspace/run.py --wallet 0x... --network base --format json",
            "daily": "python3 workspace/run.py --mode daily --wallets-file /caminho/seguro/wallets.json --format pretty",
            "runtime_status": "python3 workspace/run.py --runtime-status",
        },
        "guardrails": [
            "Somente leitura: não conecta wallet, não assina transações e não move fundos.",
            "Nunca pedir seed phrase, private key, mnemonic, token, API key ou webhook no chat.",
            "Provider DeBank é opcional e só deve ser usado se já estiver configurado no ambiente/secret manager.",
            "Não inventar preço, PnL, valuation DeFi, staking ou histórico ausente.",
            "Sinalizar cobertura parcial por rede/fonte quando necessário.",
        ],
    }
    if state["questionnaire_completed"]:
        payload["confirmation"] = (
            f"Vou consultar {state['wallet']} em {state['network']} no escopo {state['scope']}, "
            f"somente leitura, e entregar em {state['output_format']}."
        )
    return payload


def build_first_run_payload(wallet: str | None = None, network: str | None = None) -> dict[str, Any]:
    """Compatibilidade com workspace/run.py existente."""
    return build_wizard_payload(wallet=wallet, network=network)


def main() -> int:
    parser = argparse.ArgumentParser(description="Wizard chat-first da skill multichain-wallet-portfolio")
    parser.add_argument("--json", action="store_true", help="Emite payload JSON do wizard.")
    parser.add_argument("--wallet")
    parser.add_argument("--network")
    parser.add_argument("--scope")
    parser.add_argument("--output-format", choices=SUPPORTED_FORMATS)
    args = parser.parse_args()

    payload = build_wizard_payload(
        wallet=args.wallet,
        network=args.network,
        scope=args.scope,
        output_format=args.output_format,
    )
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(payload["introduction"])
        if payload.get("next_question"):
            print(payload["next_question"]["question"])
        else:
            print(payload["confirmation"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
