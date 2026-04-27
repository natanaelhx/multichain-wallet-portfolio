from __future__ import annotations

from typing import Any, Dict, List

import requests

from adapters.base import AdapterError, BaseAdapter, Coverage, PortfolioResult
from token_filters import audit_payload, classify_token, is_stable


DEFAULT_EVM_NETWORKS = {
    "ethereum",
    "base",
    "arbitrum",
    "optimism",
    "polygon",
    "bnb",
    "bsc",
    "avalanche",
    "linea",
    "scroll",
    "zksync",
    "blast",
}


class EVMAdapter(BaseAdapter):
    name = "evm"
    _ethplorer_url = "https://api.ethplorer.io/getAddressInfo/{wallet}?apiKey=freekey"
    _coingecko_price_url = "https://api.coingecko.com/api/v3/simple/price"
    _defillama_price_url = "https://coins.llama.fi/prices/current/coingecko:{coin_id}"
    _public_rpc = {
        "base": "https://base-rpc.publicnode.com",
        "arbitrum": "https://arbitrum-one-rpc.publicnode.com",
        "optimism": "https://optimism-rpc.publicnode.com",
        "polygon": "https://polygon-bor-rpc.publicnode.com",
        "bnb": "https://bsc-rpc.publicnode.com",
        "bsc": "https://bsc-rpc.publicnode.com",
        "avalanche": "https://avalanche-c-chain-rpc.publicnode.com",
    }
    _blockscout = {
        "base": "https://base.blockscout.com/api/v2/addresses/{wallet}/tokens",
        "arbitrum": "https://arbitrum.blockscout.com/api/v2/addresses/{wallet}/tokens",
        "optimism": "https://optimism.blockscout.com/api/v2/addresses/{wallet}/tokens",
        "polygon": "https://polygon.blockscout.com/api/v2/addresses/{wallet}/tokens",
    }

    def supports(self, network: str) -> bool:
        return network.strip().lower() in DEFAULT_EVM_NETWORKS

    def _fetch_ethplorer(self, wallet: str) -> Dict[str, Any]:
        try:
            response = requests.get(self._ethplorer_url.format(wallet=wallet), timeout=20)
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            raise AdapterError(f"Falha ao consultar Ethplorer: {exc}") from exc

    @staticmethod
    def _fmt_usd(value: float | None) -> str:
        if value is None:
            return "n/d"
        return f"{value:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")

    def _get_native_price(self, network: str) -> tuple[float | None, float | None, str]:
        mapping = {
            "ethereum": ("ethereum", "ETH"),
            "base": ("ethereum", "ETH"),
            "arbitrum": ("ethereum", "ETH"),
            "optimism": ("ethereum", "ETH"),
            "polygon": ("matic-network", "MATIC"),
            "bnb": ("binancecoin", "BNB"),
            "bsc": ("binancecoin", "BNB"),
            "avalanche": ("avalanche-2", "AVAX"),
        }
        coin_id, symbol = mapping.get(network, ("ethereum", "ETH"))
        try:
            response = requests.get(
                self._coingecko_price_url,
                params={"ids": coin_id, "vs_currencies": "usd", "include_24hr_change": "true"},
                timeout=20,
            )
            response.raise_for_status()
            data = response.json().get(coin_id) or {}
            price = data.get("usd")
            change = data.get("usd_24h_change")
            if price is not None:
                return price, change, symbol
        except Exception:
            pass
        try:
            response = requests.get(self._defillama_price_url.format(coin_id=coin_id), timeout=20)
            response.raise_for_status()
            coin = (response.json().get("coins") or {}).get(f"coingecko:{coin_id}") or {}
            return coin.get("price"), None, symbol
        except Exception:
            return None, None, symbol

    def _fetch_blockscout_tokens(self, wallet: str, network: str) -> List[Dict[str, Any]]:
        url = self._blockscout.get(network)
        if not url:
            return []
        try:
            response = requests.get(url.format(wallet=wallet), timeout=20, headers={"accept": "application/json"})
            response.raise_for_status()
            return response.json().get("items") or []
        except Exception:
            return []

    def _fetch_rpc_native_balance(self, wallet: str, network: str) -> float:
        rpc = self._public_rpc.get(network)
        if not rpc:
            raise AdapterError(f"Sem RPC público configurado para {network}.")
        payload = {"jsonrpc": "2.0", "method": "eth_getBalance", "params": [wallet, "latest"], "id": 1}
        try:
            response = requests.post(rpc, json=payload, timeout=20)
            response.raise_for_status()
            data = response.json()
            if data.get("error"):
                raise AdapterError(f"Erro RPC {network}: {data['error']}")
            raw = data.get("result")
            return int(raw, 16) / 1e18 if raw else 0.0
        except Exception as exc:
            raise AdapterError(f"Falha ao consultar RPC {network}: {exc}") from exc

    def _build_from_ethplorer(self, wallet: str, network: str, payload: Dict[str, Any]) -> PortfolioResult:
        eth = payload.get("ETH") or {}
        price = ((eth.get("price") or {}).get("rate"))
        diff = ((eth.get("price") or {}).get("diff"))
        eth_balance = eth.get("balance") or 0
        total_usd = (eth_balance * price) if price else 0.0
        balances: List[Dict[str, Any]] = []
        if eth_balance:
            balances.append(
                {
                    "symbol": "ETH",
                    "amount": round(eth_balance, 8),
                    "usd_value": self._fmt_usd(total_usd) if price else "n/d",
                    "change_24h": f"{diff}%" if diff is not None else "n/d",
                    "category": "l1/l2",
                }
            )

        stable_usd = 0.0
        for token in payload.get("tokens") or []:
            info = token.get("tokenInfo") or {}
            decimals_raw = info.get("decimals")
            try:
                decimals = int(decimals_raw) if decimals_raw is not None else 0
            except Exception:
                decimals = 0
            raw_balance = token.get("balance") or 0
            amount = raw_balance / (10 ** decimals) if decimals >= 0 else 0
            symbol = info.get("symbol") or "?"
            price_info = info.get("price") or {}
            token_price = price_info.get("rate") if isinstance(price_info, dict) else None
            usd_value = amount * token_price if token_price else None
            if usd_value:
                total_usd += usd_value
            if usd_value and is_stable(symbol):
                stable_usd += usd_value
            balances.append(
                {
                    "symbol": symbol,
                    "amount": round(amount, 8),
                    "usd_value": self._fmt_usd(usd_value) if usd_value is not None else "n/d",
                    "change_24h": f"{price_info.get('diff')}%" if isinstance(price_info, dict) and price_info.get("diff") is not None else "n/d",
                    "category": "stablecoins" if is_stable(symbol) else "outros",
                }
            )

        balances.sort(key=lambda item: float(str(item.get("usd_value", "0")).replace(".", "").replace(",", ".")) if item.get("usd_value") not in {None, "n/d"} else -1, reverse=True)
        top_usd = None
        if balances and balances[0].get("usd_value") not in {None, "n/d"}:
            top_usd = float(str(balances[0]["usd_value"]).replace(".", "").replace(",", "."))
        top_concentration = f"{(top_usd / total_usd * 100):.1f}%" if top_usd and total_usd > 0 else "n/d"
        stable_pct = f"{(stable_usd / total_usd * 100):.1f}%" if stable_usd and total_usd > 0 else "0%"
        diversification = "baixa" if len(balances) <= 2 else "média" if len(balances) <= 6 else "alta"

        insights = []
        if top_concentration not in {"n/d"}:
            try:
                pct = float(top_concentration.replace("%", ""))
                if pct >= 70:
                    insights.append("⚠️ Concentração alta em um único ativo.")
            except Exception:
                pass
        if stable_pct not in {"0%", "n/d"}:
            insights.append(f"🟢 Exposição relevante em stablecoins: {stable_pct}.")
        if diff is not None:
            insights.append(f"📈 ETH com variação de {diff}% nas últimas 24h.")

        return PortfolioResult(
            ok=True,
            network=network,
            wallet_input=wallet,
            wallet_resolved=payload.get("address") or wallet,
            adapter=self.name,
            summary={
                "total_usd": self._fmt_usd(total_usd),
                "change_24h": f"ETH {diff}%" if diff is not None else "parcial",
                "stablecoin_exposure": stable_pct,
                "top_concentration": top_concentration,
                "diversification": diversification,
                "categories": ["stablecoins", "l1/l2", "outros"],
            },
            balances=balances,
            positions=[],
            insights=insights or ["ℹ️ Snapshot obtido com fonte pública Ethereum."],
            actions=[
                "Revisar ativos sem preço em USD, se existirem.",
                "Adicionar fonte complementar para posições/DeFi e cobertura multi-EVM mais profunda.",
            ],
            coverage=Coverage(
                level="medium",
                summary="Ethereum com saldo e tokens via fonte pública; posições e enriquecimento multi-chain ainda são parciais.",
                sources=["Ethplorer freekey (Ethereum)"],
                limits=[
                    "Esta integração real inicial está validada para Ethereum.",
                    "Outras EVMs ainda usam a arquitetura base e precisam de fonte equivalente por rede.",
                    "Posições DeFi e 24h por posição ainda não estão integradas.",
                ],
            ),
            raw={"wallet": wallet, "network": network, "ethplorer": payload},
        )

    def collect(self, wallet: str, network: str) -> PortfolioResult:
        network = network.lower()
        if network == "ethereum":
            payload = self._fetch_ethplorer(wallet)
            return self._build_from_ethplorer(wallet, network, payload)

        native_balance = self._fetch_rpc_native_balance(wallet, network)
        native_price, native_change, native_symbol = self._get_native_price(network)
        native_usd = native_balance * native_price if native_price else None
        total_usd = native_usd or 0.0
        balances = [
            {
                "symbol": native_symbol,
                "amount": round(native_balance, 10),
                "usd_value": self._fmt_usd(native_usd) if native_usd is not None else "n/d",
                "change_24h": f"{native_change:.2f}%" if native_change is not None else "n/d",
                "category": "l1/l2",
            }
        ]
        stable_usd = 0.0
        token_items = self._fetch_blockscout_tokens(wallet, network)
        suspicious_tokens: List[Dict[str, Any]] = []
        filtered_tokens: List[Dict[str, Any]] = []
        for item in token_items[:20]:
            token = item.get("token") or {}
            symbol = token.get("symbol") or "?"
            name = token.get("name") or ""
            decimals = int(token.get("decimals") or 0)
            raw_value = int(item.get("value") or 0)
            amount = raw_value / (10 ** decimals) if decimals >= 0 else 0
            exchange_rate = token.get("exchange_rate")
            try:
                price = float(exchange_rate) if exchange_rate not in {None, ""} else None
            except Exception:
                price = None
            usd_value = amount * price if price is not None else None
            decision = classify_token(name=name, symbol=symbol, usd_value=usd_value)
            if not decision.visible:
                payload = audit_payload(
                    symbol=symbol,
                    name=name,
                    amount=round(amount, 8),
                    contract=token.get("address_hash"),
                    reason=decision.reason or "Token ocultado do output principal.",
                    usd_value=self._fmt_usd(usd_value) if usd_value is not None else None,
                )
                if decision.suspicious:
                    suspicious_tokens.append(payload)
                else:
                    filtered_tokens.append(payload)
                continue
            total_usd += usd_value or 0
            category = decision.category
            if category == "stablecoins":
                stable_usd += usd_value or 0
            balances.append(
                {
                    "symbol": symbol,
                    "amount": round(amount, 8),
                    "usd_value": self._fmt_usd(usd_value),
                    "change_24h": "n/d",
                    "category": category,
                    "contract": token.get("address_hash"),
                }
            )
        insights = [f"🌐 Saldo nativo obtido via RPC público de {network}."]
        visible_token_count = max(0, len(balances) - 1)
        if visible_token_count:
            insights.append(f"🪙 {visible_token_count} token(s) com valor relevante detectado(s) via Blockscout em {network}.")
        hidden_count = len(suspicious_tokens) + len(filtered_tokens)
        if hidden_count:
            insights.append(f"🛡️ {hidden_count} token(s) ocultado(s) do output principal por segurança/baixo valor.")
        if native_change is not None:
            insights.append(f"📈 {native_symbol} com variação de {native_change:.2f}% nas últimas 24h.")
        stable_pct = f"{(stable_usd / total_usd * 100):.1f}%" if stable_usd and total_usd > 0 else "0%"
        top_concentration = "100.0%" if len([b for b in balances if b.get("amount") not in {0, 0.0}]) == 1 and total_usd > 0 else "parcial"
        return PortfolioResult(
            ok=True,
            network=network,
            wallet_input=wallet,
            wallet_resolved=wallet,
            adapter=self.name,
            summary={
                "total_usd": self._fmt_usd(total_usd),
                "change_24h": f"{native_symbol} {native_change:.2f}%" if native_change is not None else "parcial",
                "stablecoin_exposure": stable_pct,
                "top_concentration": top_concentration,
                "diversification": "alta" if len(balances) > 10 else "média" if len(balances) > 3 else "baixa",
                "categories": ["stablecoins", "l1/l2", "outros"],
            },
            balances=balances,
            positions=[],
            insights=insights,
            actions=[
                "Adicionar fonte complementar de tokens para esta EVM.",
                "Integrar posições/DeFi e enriquecimento por rede como próximo passo.",
            ],
            coverage=Coverage(
                level="medium",
                summary="Saldo nativo e tokens ERC-20 via fontes públicas; posições DeFi ainda estão pendentes para esta EVM.",
                sources=[f"RPC público {network}", "CoinGecko público", "Blockscout público"],
                limits=[
                    "Preço/24h por token depende da cobertura do Blockscout/Coingecko.",
                    "Posições DeFi ainda não estão conectadas nesta EVM.",
                    "Tokens suspeitos são ocultados do output principal e preservados em raw.suspicious_tokens.",
                    "Tokens sem preço confiável ou abaixo de $0.01 são ocultados e preservados em raw.filtered_tokens.",
                ],
            ),
            raw={
                "wallet": wallet,
                "network": network,
                "native_balance": native_balance,
                "blockscout_tokens": token_items,
                "suspicious_tokens": suspicious_tokens,
                "filtered_tokens": filtered_tokens,
            },
        )
