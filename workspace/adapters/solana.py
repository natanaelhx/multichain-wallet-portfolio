from __future__ import annotations

from typing import Any, Dict, List

import requests

from adapters.base import AdapterError, BaseAdapter, Coverage, PortfolioResult
from token_filters import audit_payload, classify_token


class SolanaAdapter(BaseAdapter):
    name = "solana"
    _rpc_url = "https://api.mainnet-beta.solana.com"
    _coingecko_price_url = "https://api.coingecko.com/api/v3/simple/price"
    _coingecko_token_url = "https://api.coingecko.com/api/v3/simple/token_price/solana"
    _defillama_sol_price_url = "https://coins.llama.fi/prices/current/coingecko:solana"

    def supports(self, network: str) -> bool:
        return network.strip().lower() == "solana"

    def _rpc(self, method: str, params: list[Any]) -> Dict[str, Any]:
        payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
        try:
            response = requests.post(self._rpc_url, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            if data.get("error"):
                raise AdapterError(f"Erro RPC Solana: {data['error']}")
            return data.get("result") or {}
        except Exception as exc:
            raise AdapterError(f"Falha ao consultar RPC Solana: {exc}") from exc

    def _get_sol_price(self) -> tuple[float | None, float | None]:
        try:
            response = requests.get(
                self._coingecko_price_url,
                params={"ids": "solana", "vs_currencies": "usd", "include_24hr_change": "true"},
                timeout=20,
            )
            response.raise_for_status()
            data = response.json().get("solana") or {}
            price = data.get("usd")
            change = data.get("usd_24h_change")
            if price is not None:
                return price, change
        except Exception:
            pass
        try:
            response = requests.get(self._defillama_sol_price_url, timeout=20)
            response.raise_for_status()
            coin = (response.json().get("coins") or {}).get("coingecko:solana") or {}
            return coin.get("price"), None
        except Exception:
            return None, None

    def _get_token_price(self, mint: str) -> tuple[float | None, float | None]:
        try:
            response = requests.get(
                self._coingecko_token_url,
                params={
                    "contract_addresses": mint,
                    "vs_currencies": "usd",
                    "include_24hr_change": "true",
                },
                timeout=20,
            )
            response.raise_for_status()
            data = response.json().get(mint.lower()) or {}
            return data.get("usd"), data.get("usd_24h_change")
        except Exception:
            return None, None

    @staticmethod
    def _fmt_usd(value: float | None) -> str:
        if value is None:
            return "n/d"
        return f"{value:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")

    @staticmethod
    def _short_mint(mint: str) -> str:
        if len(mint) <= 12:
            return mint
        return f"{mint[:4]}...{mint[-4:]}"

    def collect(self, wallet: str, network: str) -> PortfolioResult:
        balance_result = self._rpc("getBalance", [wallet])
        token_result = self._rpc(
            "getTokenAccountsByOwner",
            [wallet, {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"}, {"encoding": "jsonParsed"}],
        )

        sol_balance = (balance_result.get("value") or 0) / 1_000_000_000
        sol_price, sol_change = self._get_sol_price()
        total_usd = sol_balance * sol_price if sol_price else 0.0
        balances: List[Dict[str, Any]] = [
            {
                "symbol": "SOL",
                "amount": round(sol_balance, 8),
                "usd_value": self._fmt_usd(total_usd) if sol_price else "n/d",
                "change_24h": f"{sol_change:.2f}%" if sol_change is not None else "n/d",
                "category": "sol",
            }
        ]

        raw_tokens = []
        for item in (token_result.get("value") or []):
            parsed = (((item.get("account") or {}).get("data") or {}).get("parsed") or {})
            info = parsed.get("info") or {}
            token_amount = info.get("tokenAmount") or {}
            mint = info.get("mint") or ""
            ui_amount = token_amount.get("uiAmount")
            if ui_amount in (None, 0):
                continue
            raw_tokens.append({
                "mint": mint,
                "amount": float(ui_amount),
            })

        raw_tokens.sort(key=lambda x: x["amount"], reverse=True)
        stable_usd = 0.0
        suspicious_tokens: List[Dict[str, Any]] = []
        filtered_tokens: List[Dict[str, Any]] = []
        for token in raw_tokens[:20]:
            price_usd, change_24h = self._get_token_price(token["mint"])
            usd_value = token["amount"] * price_usd if price_usd else None
            symbol = self._short_mint(token["mint"])
            name = token["mint"]
            decision = classify_token(name=name, symbol=symbol, usd_value=usd_value)
            if not decision.visible:
                payload = audit_payload(
                    symbol=symbol,
                    name=name,
                    amount=round(token["amount"], 8),
                    contract=token["mint"],
                    reason=decision.reason or "SPL ocultado do output principal.",
                    usd_value=self._fmt_usd(usd_value) if usd_value is not None else None,
                )
                if decision.suspicious:
                    suspicious_tokens.append(payload)
                else:
                    filtered_tokens.append(payload)
                continue
            total_usd += usd_value or 0
            if decision.category == "stablecoins":
                stable_usd += usd_value or 0
            balances.append(
                {
                    "symbol": symbol,
                    "amount": round(token["amount"], 8),
                    "usd_value": self._fmt_usd(usd_value),
                    "change_24h": f"{change_24h:.2f}%" if change_24h is not None else "n/d",
                    "category": decision.category if decision.category != "outros" else "spl",
                    "mint": token["mint"],
                }
            )

        priced_values = []
        for item in balances:
            usd = item.get("usd_value")
            if usd not in {None, "n/d"}:
                priced_values.append(float(str(usd).replace(".", "").replace(",", ".")))
        top_concentration = "n/d"
        if priced_values and total_usd > 0:
            top_concentration = f"{(max(priced_values) / total_usd * 100):.1f}%"
        diversification = "alta" if len(balances) > 10 else "média" if len(balances) > 3 else "baixa"
        stable_pct = f"{(stable_usd / total_usd * 100):.1f}%" if stable_usd and total_usd > 0 else "0%"

        insights = []
        if sol_change is not None:
            insights.append(f"📈 SOL com variação de {sol_change:.2f}% nas últimas 24h.")
        visible_spl_count = max(0, len(balances) - 1)
        if visible_spl_count > 0:
            insights.append(f"🪙 {visible_spl_count} SPL(s) com valor relevante detectado(s) via RPC público.")
        hidden_count = len(suspicious_tokens) + len(filtered_tokens)
        if hidden_count:
            insights.append(f"🛡️ {hidden_count} SPL(s) ocultado(s) do output principal por segurança/baixo valor.")
        if len(balances) > 10:
            insights.append("🧩 Diversificação alta nesta rede — mais de 10 ativos detectados.")

        return PortfolioResult(
            ok=True,
            network="solana",
            wallet_input=wallet,
            wallet_resolved=wallet,
            adapter=self.name,
            summary={
                "total_usd": self._fmt_usd(total_usd),
                "change_24h": f"SOL {sol_change:.2f}%" if sol_change is not None else "parcial",
                "stablecoin_exposure": stable_pct,
                "top_concentration": top_concentration,
                "diversification": diversification,
                "categories": ["sol", "spl", "staking", "defi", "outros"],
            },
            balances=balances,
            positions=[],
            insights=insights or ["ℹ️ Snapshot Solana obtido com RPC público."],
            actions=[
                "Adicionar camada de metadata/token symbols para melhorar leitura dos SPLs.",
                "Integrar staking/DeFi e preços mais completos como próximo passo da trilha Solana.",
            ],
            coverage=Coverage(
                level="medium",
                summary="SOL e SPL balances via RPC público; preços e enriquecimento seguem parciais conforme disponibilidade pública.",
                sources=["RPC público Solana", "CoinGecko público"],
                limits=[
                    "Símbolos de SPL podem aparecer como mint encurtado nesta base inicial.",
                    "Staking e posições DeFi ainda não estão integrados nesta primeira versão real.",
                    "Preço em USD depende de cobertura pública por token.",
                    "SPLs sem preço confiável ou abaixo de $0.01 são ocultados e preservados em raw.filtered_tokens.",
                ],
            ),
            raw={
                "wallet": wallet,
                "balance_result": balance_result,
                "token_result": token_result,
                "suspicious_tokens": suspicious_tokens,
                "filtered_tokens": filtered_tokens,
            },
        )
