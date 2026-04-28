from __future__ import annotations

from datetime import datetime, timezone
import time
from typing import Any, Dict, List

from requests_compat import requests

from adapters.base import AdapterError, BaseAdapter, Coverage, PortfolioResult
from token_filters import audit_payload, classify_token


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

    @staticmethod
    def _parse_float(value: Any) -> float | None:
        try:
            if value in {None, "", "n/d"}:
                return None
            return float(value)
        except Exception:
            return None

    @classmethod
    def _fmt_pct(cls, value: float | None) -> str:
        if value is None:
            return "n/d"
        return f"{value:.2f}%"

    @classmethod
    def _asset_contexts(cls, meta_and_ctxs: Any) -> Dict[str, Dict[str, Any]]:
        if not isinstance(meta_and_ctxs, list) or len(meta_and_ctxs) < 2:
            return {}
        meta = meta_and_ctxs[0] if isinstance(meta_and_ctxs[0], dict) else {}
        universe = meta.get("universe") or []
        contexts = meta_and_ctxs[1] if isinstance(meta_and_ctxs[1], list) else []
        result: Dict[str, Dict[str, Any]] = {}
        for index, asset in enumerate(universe):
            if not isinstance(asset, dict):
                continue
            name = asset.get("name")
            ctx = contexts[index] if index < len(contexts) and isinstance(contexts[index], dict) else {}
            if name:
                result[str(name)] = ctx
        return result

    def _safe_post(self, payload: Dict[str, Any], fallback: Any) -> Any:
        try:
            return self._post(payload)
        except Exception:
            return fallback

    @classmethod
    def _portfolio_periods(cls, portfolio: Any) -> Dict[str, Dict[str, Any]]:
        if not isinstance(portfolio, list):
            return {}
        result: Dict[str, Dict[str, Any]] = {}
        for item in portfolio:
            if isinstance(item, list) and len(item) == 2 and isinstance(item[1], dict):
                result[str(item[0])] = item[1]
        return result

    @classmethod
    def _last_series_value(cls, series: Any) -> float | None:
        if not isinstance(series, list) or not series:
            return None
        return cls._parse_float(series[-1][1] if isinstance(series[-1], list) and len(series[-1]) > 1 else None)

    @classmethod
    def _series_delta_since(cls, series: Any, cutoff_ms: int) -> float | None:
        if not isinstance(series, list) or len(series) < 2:
            return None
        latest = cls._parse_float(series[-1][1] if isinstance(series[-1], list) and len(series[-1]) > 1 else None)
        if latest is None:
            return None
        base = None
        for point in series:
            if not isinstance(point, list) or len(point) < 2:
                continue
            ts = point[0]
            if isinstance(ts, int) and ts <= cutoff_ms:
                base = cls._parse_float(point[1])
        if base is None:
            base = cls._parse_float(series[0][1] if isinstance(series[0], list) and len(series[0]) > 1 else None)
        return latest - base if base is not None else None

    @classmethod
    def _fmt_timestamp(cls, ms: int | None) -> str:
        if not ms:
            return "n/d"
        return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%d/%m/%Y %H:%M UTC")

    @classmethod
    def _fmt_duration(cls, start_ms: int | None, end_ms: int | None = None) -> str:
        if not start_ms:
            return "n/d"
        end_ms = end_ms or int(time.time() * 1000)
        total_hours = max(0, int((end_ms - start_ms) / 3_600_000))
        days, hours = divmod(total_hours, 24)
        if days:
            return f"{days}d {hours}h"
        return f"{hours}h"

    @classmethod
    def _position_opened_at(cls, coin: str, fills: Any) -> tuple[int | None, str]:
        if not isinstance(fills, list):
            return None, "none"
        coin_fills = [item for item in fills if isinstance(item, dict) and item.get("coin") == coin]
        if not coin_fills:
            return None, "none"
        coin_fills.sort(key=lambda item: item.get("time") or 0)
        candidate = None
        for fill in coin_fills:
            start_position = cls._parse_float(fill.get("startPosition"))
            direction = str(fill.get("dir") or "")
            if start_position is not None and abs(start_position) < 1e-9 and direction.startswith("Open"):
                candidate = fill.get("time")
        if candidate:
            return int(candidate), "high"
        earliest = coin_fills[0].get("time")
        return (int(earliest), "lower_bound") if earliest else (None, "none")

    @classmethod
    def _funding_total(cls, funding_rows: Any) -> float | None:
        if not isinstance(funding_rows, list):
            return None
        total = 0.0
        seen = False
        for item in funding_rows:
            if not isinstance(item, dict):
                continue
            delta = item.get("delta") if isinstance(item.get("delta"), dict) else {}
            value = cls._parse_float(delta.get("usdc"))
            if value is not None:
                total += value
                seen = True
        return total if seen else None

    def collect(self, wallet: str, network: str) -> PortfolioResult:
        state = self._post({"type": "clearinghouseState", "user": wallet})
        spot_state = self._post({"type": "spotClearinghouseState", "user": wallet})
        open_orders = self._post({"type": "openOrders", "user": wallet})
        now_ms = int(time.time() * 1000)
        portfolio = self._safe_post({"type": "portfolio", "user": wallet}, [])
        portfolio_periods = self._portfolio_periods(portfolio)
        fills_7d = self._safe_post({"type": "userFillsByTime", "user": wallet, "startTime": now_ms - 7 * 86_400_000}, [])
        funding_7d = self._safe_post({"type": "userFunding", "user": wallet, "startTime": now_ms - 7 * 86_400_000}, [])
        try:
            asset_contexts = self._asset_contexts(self._post({"type": "metaAndAssetCtxs"}))
        except Exception:
            asset_contexts = {}

        margin = state.get("marginSummary") or {}
        account_value = float(margin.get("accountValue") or 0)
        total_ntl = float(margin.get("totalNtlPos") or 0)
        withdrawable = float(state.get("withdrawable") or 0)
        positions_raw = state.get("assetPositions") or []
        spot_balances_raw = spot_state.get("balances") or []

        positions: List[Dict[str, Any]] = []
        position_pnl_values: List[float] = []
        for item in positions_raw:
            pos = item.get("position") or item
            if not isinstance(pos, dict):
                continue
            coin = pos.get("coin") or pos.get("asset") or "position"
            ctx = asset_contexts.get(str(coin), {})
            mark_px = self._parse_float(ctx.get("markPx"))
            prev_day_px = self._parse_float(ctx.get("prevDayPx"))
            market_change_24h = None
            if mark_px is not None and prev_day_px not in {None, 0}:
                market_change_24h = ((mark_px - prev_day_px) / prev_day_px) * 100
            opened_at_ms, opened_confidence = self._position_opened_at(str(coin), fills_7d)
            position_value = self._parse_float(pos.get("positionValue") or pos.get("notional"))
            unrealized_pnl = self._parse_float(pos.get("unrealizedPnl"))
            if unrealized_pnl is not None:
                position_pnl_values.append(unrealized_pnl)
            return_on_equity = self._parse_float(pos.get("returnOnEquity"))
            positions.append(
                {
                    "name": coin,
                    "size": pos.get("szi") or pos.get("size") or "n/d",
                    "entry_px": pos.get("entryPx") or "n/d",
                    "usd_value": self._fmt_usd(position_value),
                    "change_24h": self._fmt_pct(market_change_24h),
                    "unrealized_pnl_usd": self._fmt_usd(unrealized_pnl),
                    "return_on_equity": self._fmt_pct(return_on_equity * 100 if return_on_equity is not None else None),
                    "mark_px": mark_px if mark_px is not None else "n/d",
                    "prev_day_px": prev_day_px if prev_day_px is not None else "n/d",
                    "opened_at": self._fmt_timestamp(opened_at_ms),
                    "open_duration": self._fmt_duration(opened_at_ms, now_ms),
                    "entry_time_confidence": opened_confidence,
                    "funding": ctx.get("funding") or "n/d",
                    "leverage": pos.get("leverage") or "n/d",
                }
            )

        balances: List[Dict[str, Any]] = []
        suspicious_tokens: List[Dict[str, Any]] = []
        filtered_tokens: List[Dict[str, Any]] = []
        for item in spot_balances_raw:
            coin = item.get("coin") or item.get("token") or "spot"
            total = item.get("total") or item.get("balance") or item.get("hold") or "n/d"
            amount = self._parse_float(total)
            price_usd = 1.0 if str(coin).upper() == "USDC" else None
            usd_value = amount * price_usd if amount is not None and price_usd is not None else None
            decision = classify_token(name=str(coin), symbol=str(coin), usd_value=usd_value)
            if not decision.visible:
                payload = audit_payload(
                    symbol=str(coin),
                    name=str(coin),
                    amount=amount or 0.0,
                    contract=item.get("token") or item.get("coin"),
                    reason=decision.reason or "Spot token Hyperliquid ocultado do output principal.",
                    usd_value=self._fmt_usd(usd_value) if usd_value is not None else None,
                )
                if decision.suspicious:
                    suspicious_tokens.append(payload)
                else:
                    filtered_tokens.append(payload)
                continue
            balances.append(
                {
                    "symbol": coin,
                    "amount": total,
                    "usd_value": self._fmt_usd(usd_value),
                    "change_24h": "n/d",
                    "category": decision.category if decision.category != "outros" else "spot",
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
            if position_pnl_values:
                insights.append(f"💹 PnL não realizado total das posições: ${self._fmt_usd(sum(position_pnl_values))}.")
        if orders:
            insights.append(f"🧾 {len(orders)} ordem(ns) aberta(s) identificada(s) na Hyperliquid.")
        hidden_count = len(suspicious_tokens) + len(filtered_tokens)
        if hidden_count:
            insights.append(f"🛡️ {hidden_count} spot token(s) ocultado(s) do output principal por falta de preço confiável/baixo valor.")

        perp_day = portfolio_periods.get("perpDay") or portfolio_periods.get("day") or {}
        perp_week = portfolio_periods.get("perpWeek") or portfolio_periods.get("week") or {}
        perp_all_time = portfolio_periods.get("perpAllTime") or portfolio_periods.get("allTime") or {}
        pnl_24h = self._last_series_value(perp_day.get("pnlHistory"))
        pnl_48h = self._series_delta_since(perp_week.get("pnlHistory"), now_ms - 2 * 86_400_000)
        pnl_7d = self._last_series_value(perp_week.get("pnlHistory"))
        pnl_all_time = self._last_series_value(perp_all_time.get("pnlHistory"))
        funding_7d_total = self._funding_total(funding_7d)
        if any(value is not None for value in [pnl_24h, pnl_48h, pnl_7d, pnl_all_time]):
            insights.append(
                "📊 PnL períodos — "
                f"24h: ${self._fmt_usd(pnl_24h)} | "
                f"48h: ${self._fmt_usd(pnl_48h)} | "
                f"7d: ${self._fmt_usd(pnl_7d)} | "
                f"total: ${self._fmt_usd(pnl_all_time)}."
            )
        if funding_7d_total is not None:
            insights.append(f"💸 Funding 7d: ${self._fmt_usd(funding_7d_total)}.")

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
                "pnl_24h_usd": self._fmt_usd(pnl_24h),
                "pnl_48h_usd": self._fmt_usd(pnl_48h),
                "pnl_7d_usd": self._fmt_usd(pnl_7d),
                "pnl_all_time_usd": self._fmt_usd(pnl_all_time),
                "funding_7d_usd": self._fmt_usd(funding_7d_total),
            },
            balances=balances,
            positions=positions,
            orders=orders,
            insights=insights or ["ℹ️ Snapshot Hyperliquid obtido via API pública."],
            actions=[
                "Se esperado, validar se esta é mesmo a conta Hyperliquid correta associada ao endereço.",
                "Validar PnL/mark price das posições antes de usar como base operacional de decisão.",
            ],
            coverage=Coverage(
                level="medium",
                summary="Equity, posições, PnL não realizado, PnL por período, mark price, variação 24h de mercado, histórico de fills e ordens abertas integrados via API pública Hyperliquid.",
                sources=["API pública Hyperliquid", "Hyperliquid metaAndAssetCtxs", "Hyperliquid portfolio", "Hyperliquid userFillsByTime", "Hyperliquid userFunding"],
                limits=[
                    "change_24h em posições representa variação 24h do mercado/ativo, não PnL realizado da posição.",
                    "opened_at é estimado por fills dos últimos 7 dias; se a posição for mais antiga, é lower_bound.",
                    "PnL 48h é calculado por delta aproximado da série de PnL semanal pública.",
                    "Spot tokens sem preço confiável ou abaixo de $0.01 são ocultados e preservados em raw.filtered_tokens.",
                    "USDC spot é tratado como USD 1 quando disponível; demais preços spot ainda precisam de enriquecimento.",
                ],
            ),
            raw={
                "wallet": wallet,
                "state": state,
                "spot_state": spot_state,
                "open_orders": open_orders,
                "asset_contexts": asset_contexts,
                "portfolio": portfolio,
                "fills_7d": fills_7d,
                "funding_7d": funding_7d,
                "suspicious_tokens": suspicious_tokens,
                "filtered_tokens": filtered_tokens,
            },
        )
