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
    """Render single-wallet analysis in the same final text format used by daily cron.

    Keeping single and daily outputs aligned prevents the interactive path from
    drifting back to the older raw/debug-style format.
    """
    return render_daily_summary([result])


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


def _fmt_amount(value: Any) -> str:
    if value in {None, "", "n/d"}:
        return "n/d"
    try:
        number = float(str(value).replace(".", "").replace(",", ".")) if "," in str(value) else float(value)
    except Exception:
        return str(value)
    if number == 0:
        return "0"
    formatted = f"{number:,.10f}".rstrip("0").rstrip(".")
    return formatted.replace(",", "_").replace(".", ",").replace("_", ".")


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


def _daily_priced_balances(result: PortfolioResult) -> List[Dict[str, Any]]:
    """Balances safe to show in the daily summary.

    The daily report is user-facing and must not be polluted by spam/dust assets
    or balances without reliable USD pricing. Keep partial/unpriced tokens in raw
    audit payloads instead of the main textual summary.
    """
    visible = []
    for item in result.balances:
        usd = _parse_usd(item.get("usd_value"))
        if usd is None or usd <= 0:
            continue
        visible.append(item)
    return visible


def has_relevant_value(result: PortfolioResult) -> bool:
    total = _parse_usd(result.summary.get("total_usd"))
    if total is not None and total > 0:
        return True
    if _daily_priced_balances(result):
        return True
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

    if not visible:
        lines.extend([
            "",
            "Nenhuma wallet com saldo/preço confiável foi configurada para o resumo diário.",
            "",
            "## 📌 Ações sugeridas",
            "- preencher uma config local fora do Git com wallets reais",
            "- rodar novamente com `--wallets-file /caminho/seguro/wallets.json`",
        ])
        return "\n".join(lines).strip()

    for result in visible:
        priced_balances = _daily_priced_balances(result)
        if not priced_balances and not result.positions:
            continue
        lines.extend(["", f"### {_network_icon(result.network)} {_network_label(result.network)}"])
        for item in priced_balances:
            usd_value = f"${item.get('usd_value')}"
            change = item.get("change_24h") or "n/d"
            symbol = item.get("symbol", "?")
            amount = _fmt_amount(item.get("amount", "n/d"))
            lines.extend([
                f"**📊 {symbol} — {date_label} | {usd_value} | 24h: {change}**",
                f"• **{amount} {symbol}**",
                "",
            ])
        for position in result.positions:
            name = position.get("name", "POSITION")
            usd_value = position.get("usd_value") or "parcial"
            change = position.get("change_24h") or "n/d"
            size = _fmt_amount(position.get("size", "n/d"))
            pnl = position.get("unrealized_pnl_usd")
            pnl_suffix = f" | PnL: ${pnl}" if pnl and pnl != "n/d" else ""
            opened = position.get("open_duration")
            opened_suffix = f" | aberta há {opened}" if opened and opened != "n/d" else ""
            lines.extend([
                f"**📊 {name} — {date_label} | ${usd_value} | 24h: {change}{pnl_suffix}**",
                f"• **posição: {size} {name}{opened_suffix}**",
                "",
            ])

    insights = []
    if visible:
        top = max(visible, key=lambda r: _parse_usd(r.summary.get("total_usd")) or 0)
        if (_parse_usd(top.summary.get("total_usd")) or 0) > 0:
            insights.append(f"📈 maior peso atual está em **{_network_label(top.network)}**")
    for result in visible:
        for item in result.insights:
            if item not in insights:
                insights.append(item)
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
