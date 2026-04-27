from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Iterable, List

from adapters.base import PortfolioResult


EMOJI = {
    "value": "💼",
    "change": "📈",
    "network": "🌐",
    "coverage": "⚠️",
    "stable": "🟢",
    "risk": "🎯",
    "positions": "📌",
    "diversification": "🧩",
}


def render_pretty(result: PortfolioResult) -> str:
    summary = result.summary
    lines = [
        f"{EMOJI['value']} Valor total estimado: {summary.get('total_usd', 'n/d')}",
        f"{EMOJI['change']} Variação 24h: {summary.get('change_24h', 'n/d')}",
        f"{EMOJI['network']} Rede: {result.network}",
        f"{EMOJI['coverage']} Cobertura: {result.coverage.level} — {result.coverage.summary}",
        f"{EMOJI['stable']} Stablecoins: {summary.get('stablecoin_exposure', 'n/d')}",
        f"{EMOJI['risk']} Concentração: {summary.get('top_concentration', 'n/d')}",
        f"{EMOJI['diversification']} Diversificação: {summary.get('diversification', 'n/d')}",
    ]
    if result.balances:
        lines.append("\nAtivos principais:")
        for item in result.balances[:5]:
            lines.append(f"- {item.get('symbol','?')}: {item.get('amount','n/d')} | USD {item.get('usd_value','n/d')} | 24h {item.get('change_24h','n/d')}")
    if result.positions:
        lines.append("\nPosições:")
        for item in result.positions[:5]:
            lines.append(f"- {item.get('name','?')}: USD {item.get('usd_value','n/d')} | 24h {item.get('change_24h','n/d')}")
    if result.orders:
        lines.append("\nOrdens abertas:")
        for item in result.orders[:5]:
            lines.append(f"- {item.get('market','?')} {item.get('side','?')} {item.get('size','n/d')} @ {item.get('price','n/d')}")
    if result.insights:
        lines.append("\nInsights:")
        for item in result.insights:
            lines.append(f"- {item}")
    if result.actions:
        lines.append("\nAções sugeridas:")
        for item in result.actions:
            lines.append(f"- {item}")
    if result.coverage.limits:
        lines.append("\nLimites:")
        for item in result.coverage.limits:
            lines.append(f"- {item}")
    return "\n".join(lines)


def to_json_dict(result: PortfolioResult) -> Dict[str, Any]:
    return {
        "ok": result.ok,
        "network": result.network,
        "wallet_input": result.wallet_input,
        "wallet_resolved": result.wallet_resolved,
        "adapter": result.adapter,
        "summary": result.summary,
        "balances": result.balances,
        "positions": result.positions,
        "orders": result.orders,
        "nft_summary": result.nft_summary,
        "insights": result.insights,
        "actions": result.actions,
        "coverage": {
            "level": result.coverage.level,
            "summary": result.coverage.summary,
            "sources": result.coverage.sources,
            "limits": result.coverage.limits,
        },
        "raw": result.raw,
    }


def render_json(result: PortfolioResult) -> str:
    return json.dumps(to_json_dict(result), ensure_ascii=False, indent=2)


def _parse_usd(raw: Any) -> float | None:
    if raw in {None, "n/d", "parcial", "USD parcial"}:
        return None
    text = str(raw).replace("$", "").strip()
    try:
        return float(text.replace(".", "").replace(",", "."))
    except Exception:
        return None


def _fmt_usd(value: float | None) -> str:
    if value is None:
        return "parcial"
    return f"{value:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


def _today_brt() -> str:
    return datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=-3))).strftime("%d/%m")


def _network_icon(network: str) -> str:
    icons = {
        "ethereum": "◈",
        "base": "⛓️",
        "arbitrum": "◉",
        "optimism": "🔴",
        "polygon": "🟣",
        "bnb": "🟡",
        "bsc": "🟡",
        "solana": "◎",
        "hyperliquid": "✦",
    }
    return icons.get(network.lower(), "🌐")


def _network_label(network: str) -> str:
    labels = {
        "ethereum": "Ethereum",
        "base": "Base",
        "arbitrum": "Arbitrum",
        "optimism": "Optimism",
        "polygon": "Polygon",
        "bnb": "BNB Chain",
        "bsc": "BNB Chain",
        "solana": "Solana",
        "hyperliquid": "Hyperliquid",
    }
    return labels.get(network.lower(), network.title())


def has_relevant_value(result: PortfolioResult) -> bool:
    total = _parse_usd(result.summary.get("total_usd"))
    if total is not None and total > 0:
        return True
    for item in result.balances:
        amount = item.get("amount")
        try:
            if float(amount) > 0 and item.get("usd_value") not in {"0,00", "$0,00", "0.00"}:
                return True
        except Exception:
            continue
    return bool(result.positions or result.orders)


def render_daily_summary(results: Iterable[PortfolioResult]) -> str:
    date_label = _today_brt()
    visible: List[PortfolioResult] = [r for r in results if r.ok and has_relevant_value(r)]
    totals = [_parse_usd(r.summary.get("total_usd")) for r in visible]
    total_known = sum(v for v in totals if v is not None)
    has_partial = any(v is None for v in totals)
    coverage = "média" if visible else "baixa"

    lines = [
        f"# 💼 Portfólio — {date_label}",
        "",
        f"**💰 Total estimado:** **${_fmt_usd(total_known)}**" + (" + parcial" if has_partial else ""),
        "**📈 Variação total 24h:** **parcial**",
        f"**⚠️ Cobertura:** **{coverage}**",
        "",
        "---",
    ]

    for result in visible:
        lines.extend(["", f"### {_network_icon(result.network)} {_network_label(result.network)}"])
        for item in result.balances:
            usd_value = item.get("usd_value") or "USD parcial"
            if usd_value == "n/d":
                usd_value = "USD parcial"
            else:
                usd_value = f"${usd_value}"
            change = item.get("change_24h") or "n/d"
            symbol = item.get("symbol", "?")
            amount = item.get("amount", "n/d")
            lines.extend([
                f"**📊 {symbol} — {date_label} | {usd_value} | 24h: {change}**",
                f"• **{amount} {symbol}**",
                "",
            ])
        for position in result.positions:
            name = position.get("name", "POSITION")
            usd_value = position.get("usd_value") or "parcial"
            change = position.get("change_24h") or "n/d"
            size = position.get("size", "n/d")
            lines.extend([
                f"**📊 {name} — {date_label} | ${usd_value} | 24h: {change}**",
                f"• **posição: {size}**",
                "",
            ])

    insights = []
    if visible:
        top = max(visible, key=lambda r: _parse_usd(r.summary.get("total_usd")) or 0)
        if (_parse_usd(top.summary.get("total_usd")) or 0) > 0:
            insights.append(f"📈 maior peso atual está em **{_network_label(top.network)}**")
    insights.append("⚠️ ainda faltam DeFi, staking e pricing completo em parte das redes")

    lines.extend(["---", "", "## 🧠 Insights"])
    lines.extend([f"- {item}" for item in insights])
    lines.extend(["", "---", "", "## ⚠️ Cobertura por rede"])
    for result in visible:
        lines.append(f"- **{_network_label(result.network)}:** {result.coverage.summary}")
    lines.extend(["", "---", "", "## 📌 Ações sugeridas"])
    actions = []
    for result in visible:
        for action in result.actions:
            if action not in actions:
                actions.append(action)
    if not actions:
        actions = ["consolidar snapshot diário automático"]
    lines.extend([f"- {item}" for item in actions[:5]])
    return "\n".join(lines).strip()
