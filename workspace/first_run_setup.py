from __future__ import annotations


def explain_workflow() -> list[str]:
    return [
        "Explicar rapidamente que a skill faz leitura de portfolio e nao move fundos.",
        "Preparar automaticamente o venv local da skill quando o runtime ainda nao tiver as dependencias.",
        "Pedir primeiro a wallet que sera analisada.",
        "Autodetectar a rede quando possivel e confirmar quando houver ambiguidade.",
        "Coletar dados pelos adapters de EVM, Solana ou Hyperliquid.",
        "Consolidar USD, variacao 24h, concentracao, categorias, cobertura e limites reais.",
        "Entregar resumo executivo e proximos passos sem inventar dados ausentes.",
    ]


def build_first_run_payload(wallet: str | None = None, network: str | None = None) -> dict:
    next_question = "🔎 Qual wallet voce quer analisar?"
    if wallet and not network:
        next_question = "🌐 Quer que eu autodetecte a rede ou voce prefere informar Ethereum, Base, Solana, Hyperliquid ou outra suportada?"

    return {
        "ok": True,
        "mode": "portfolio",
        "workflow": explain_workflow(),
        "required_fields": ["wallet"],
        "optional_fields": ["network", "mode", "format"],
        "wallet": wallet,
        "network": network,
        "question_strategy": {
            "one_question_at_a_time": True,
            "use_emoji": True,
            "justify_briefly": True,
        },
        "next_question": next_question,
        "notes": [
            "Fluxo MQC: explicar o que sera feito antes da primeira pergunta.",
            "Se a wallet vier sem rede e houver ambiguidade, perguntar rede antes de executar.",
            "Nao pedir dados sensiveis nem seed phrase.",
        ],
    }
