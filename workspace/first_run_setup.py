from __future__ import annotations


def explain_workflow() -> list[str]:
    return [
        "Explicar rapidamente que a skill faz leitura de portfolio e nao move fundos.",
        "Preparar automaticamente o venv local da skill quando o runtime ainda nao tiver as dependencias.",
        "Confirmar wallet e rede, ou autodetectar quando possivel.",
        "Coletar dados pelos adapters de EVM, Solana ou Hyperliquid.",
        "Consolidar USD, variacao 24h, concentracao, categorias e cobertura.",
        "Entregar resumo executivo, blocos detalhados e proximos passos quando fizer sentido.",
    ]


def build_first_run_payload(wallet: str | None = None, network: str | None = None) -> dict:
    return {
        "ok": True,
        "mode": "portfolio",
        "workflow": explain_workflow(),
        "required_fields": ["wallet"],
        "optional_fields": ["network"],
        "wallet": wallet,
        "network": network,
    }
