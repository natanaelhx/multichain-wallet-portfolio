from __future__ import annotations

from typing import Any, Dict, List

import requests

from adapters.base import AdapterError, BaseAdapter, Coverage, PortfolioResult


class HyperliquidAdapter(BaseAdapter):
    name = "hyperliquid"
    _info_url = "https://api.hyperliquid.xyz/info"

    def supports(self, network: str) -> bool:
        return network.strip().lower() == "hyperliquid"

    def _post(self, payload: Dict[str, Any]) -> Any:
        try:
            response = requests.post(self._info_url, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            raise AdapterError(f"Falha ao consultar Hyperliquid: {exc}") from exc

    @staticmethod
    def _fmt_usd(value: float | None) -> str:
        if value is None:
            return "n/d"
        return f"{value:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")

    def collect(self, wallet: str, network: str) -> PortfolioResult:
        state = self._post({"type": "clearinghouseState", "user": wallet})
        spot_state = self._post({"type": "spotClearinghouseState", "user": wallet})
        open_orders = self._post({"type": "openOrders", "user": wallet})

        margin = state.get("marginSummary") or {}
        account_value = float(margin.get("accountValue") or 0)
        total_ntl = float(margin.get("totalNtlPos") or 0)
        withdrawable = float(state.get("withdrawable") or 0)
        positions_raw = state.get("assetPositions") or []
        spot_balances_raw = spot_state.get("balances") or []

        positions: List[Dict[str, Any]] = []
        for item in positions_raw:
            pos = item.get("position") or item
            if not isinstance(pos, dict):
                continue
            positions.append(
                {
                    "name": pos.get("coin") or pos.get("asset") or "position",
                    "size": pos.get("szi") or pos.get("size") or "n/d",
                    "entry_px": pos.get("entryPx") or "n/d",
                    "usd_value": pos.get("positionValue") or pos.get("notional") or "n/d",
                    "change_24h": "n/d",
                    "leverage": pos.get("leverage") or "n/d",
                }
            )

        balances: List[Dict[str, Any]] = []
        for item in spot_balances_raw:
            coin = item.get("coin") or item.get("token") or "spot"
            total = item.get("total") or item.get("balance") or item.get("hold") or "n/d"
            balances.append(
                {
                    "symbol": coin,
                    "amount": total,
                    "usd_value": "n/d",
                    "change_24h": "n/d",
                    "category": "spot",
                }
            )

        orders: List[Dict[str, Any]] = []
        for item in open_orders if isinstance(open_orders, list) else []:
            orders.append(
                {
                    "market": item.get("coin") or item.get("asset") or "order",
                    "side": item.get("side") or "n/d",
                    "size": item.get("sz") or item.get("size") or "n/d",
                    "price": item.get("limitPx") or item.get("px") or "n/d",
                }
            )

        insights = []
        if account_value == 0 and not positions and not orders and not balances:
            insights.append("ℹ️ Nenhuma atividade ou saldo relevante encontrado nesta conta Hyperliquid.")
        if positions:
            insights.append(f"📌 {len(positions)} posição(ões) aberta(s) identificada(s) na Hyperliquid.")
        if orders:
            insights.append(f"🧾 {len(orders)} ordem(ns) aberta(s) identificada(s) na Hyperliquid.")

        return PortfolioResult(
            ok=True,
            network="hyperliquid",
            wallet_input=wallet,
            wallet_resolved=wallet,
            adapter=self.name,
            summary={
                "total_usd": self._fmt_usd(account_value),
                "change_24h": "parcial",
                "stablecoin_exposure": "n/d",
                "top_concentration": "n/d",
                "diversification": "baixa" if len(positions) + len(balances) <= 2 else "média",
                "categories": ["perps", "derivativos", "spot", "outros"],
                "withdrawable_usd": self._fmt_usd(withdrawable),
                "notional_open_positions": self._fmt_usd(total_ntl),
            },
            balances=balances,
            positions=positions,
            orders=orders,
            insights=insights or ["ℹ️ Snapshot Hyperliquid obtido via API pública."],
            actions=[
                "Se esperado, validar se esta é mesmo a conta Hyperliquid correta associada ao endereço.",
                "Adicionar enriquecimento de PnL e variação 24h por posição em etapa posterior.",
            ],
            coverage=Coverage(
                level="medium",
                summary="Equity, posições e ordens abertas já integradas via API pública Hyperliquid; PnL e 24h detalhados ainda são parciais.",
                sources=["API pública Hyperliquid"],
                limits=[
                    "Variação 24h por posição ainda não está enriquecida nesta versão inicial.",
                    "Preços spot/derivativos detalhados ainda não foram normalizados na resposta.",
                ],
            ),
            raw={
                "wallet": wallet,
                "state": state,
                "spot_state": spot_state,
                "open_orders": open_orders,
            },
        )
