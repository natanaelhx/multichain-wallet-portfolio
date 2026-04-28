from __future__ import annotations

import os
from typing import Any, Dict, List

from requests_compat import requests

from adapters.base import AdapterError, BaseAdapter, Coverage, PortfolioResult
from token_filters import audit_payload, classify_token


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
    _dexscreener_token_url = "https://api.dexscreener.com/latest/dex/tokens/{contract}"
    _debank_complex_protocols_url = "https://pro-openapi.debank.com/v1/user/complex_protocol_list"
    _debank_chain_ids = {
        "ethereum": "eth",
        "base": "base",
        "arbitrum": "arb",
        "optimism": "op",
        "polygon": "matic",
        "bnb": "bsc",
        "bsc": "bsc",
        "avalanche": "avax",
    }
    _public_rpc = {
        "ethereum": "https://ethereum-rpc.publicnode.com",
        "base": "https://base-rpc.publicnode.com",
        "arbitrum": "https://arbitrum-one-rpc.publicnode.com",
        "optimism": "https://optimism-rpc.publicnode.com",
        "polygon": "https://polygon-bor-rpc.publicnode.com",
        "bnb": "https://bsc-rpc.publicnode.com",
        "bsc": "https://bsc-rpc.publicnode.com",
        "avalanche": "https://avalanche-c-chain-rpc.publicnode.com",
    }
    _public_rpc_fallbacks = {
        "ethereum": ["https://ethereum-rpc.publicnode.com", "https://eth.llamarpc.com"],
        "base": ["https://base-rpc.publicnode.com", "https://mainnet.base.org"],
        "arbitrum": ["https://arbitrum-one-rpc.publicnode.com", "https://arb1.arbitrum.io/rpc"],
        "optimism": ["https://optimism-rpc.publicnode.com", "https://mainnet.optimism.io"],
        "polygon": ["https://polygon-bor-rpc.publicnode.com", "https://polygon-rpc.com"],
        "bnb": ["https://bsc-rpc.publicnode.com", "https://bsc-dataseed.binance.org"],
        "bsc": ["https://bsc-rpc.publicnode.com", "https://bsc-dataseed.binance.org"],
        "avalanche": ["https://avalanche-c-chain-rpc.publicnode.com", "https://api.avax.network/ext/bc/C/rpc"],
    }
    _blockscout = {
        "ethereum": "https://eth.blockscout.com/api/v2/addresses/{wallet}/tokens",
        "base": "https://base.blockscout.com/api/v2/addresses/{wallet}/tokens",
        "arbitrum": "https://arbitrum.blockscout.com/api/v2/addresses/{wallet}/tokens",
        "optimism": "https://optimism.blockscout.com/api/v2/addresses/{wallet}/tokens",
        "polygon": "https://polygon.blockscout.com/api/v2/addresses/{wallet}/tokens",
    }
    _aave_v3_markets = {
        # Addresses sourced from the official Aave address-book. Calls are read-only.
        "ethereum": {
            "pool": "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
            "data_provider": "0x0a16f2FCC0D44FaE41cc54e079281D84A363bECD",
        },
        "base": {
            "pool": "0xA238Dd80C259a72e81d7e4664a9801593F98d1c5",
            "data_provider": "0x0F43731EB8d45A581f4a36DD74F5f358bc90C73A",
        },
        "arbitrum": {
            "pool": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
            "data_provider": "0x243Aa95cAC2a25651eda86e80bEe66114413c43b",
        },
        "optimism": {
            "pool": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
            "data_provider": "0x243Aa95cAC2a25651eda86e80bEe66114413c43b",
        },
        "polygon": {
            "pool": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
            "data_provider": "0x243Aa95cAC2a25651eda86e80bEe66114413c43b",
        },
        "bnb": {
            "pool": "0x6807dc923806fE8Fd134338EABCA509979a7e0cB",
            "data_provider": "0xc90Df74A7c16245c5F5C5870327Ceb38Fe5d5328",
        },
        "bsc": {
            "pool": "0x6807dc923806fE8Fd134338EABCA509979a7e0cB",
            "data_provider": "0xc90Df74A7c16245c5F5C5870327Ceb38Fe5d5328",
        },
        "avalanche": {
            "pool": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
            "data_provider": "0x243Aa95cAC2a25651eda86e80bEe66114413c43b",
        },
    }
    _aave_selectors = {
        "get_all_reserves_tokens": "0xb316ff89",
        "get_user_reserve_data": "0x28dd2d01",
        "decimals": "0x313ce567",
        "symbol": "0x95d89b41",
    }
    _compound_v3_markets = {
        "ethereum": [
            {"name": "USDC", "comet": "0xc3d688B66703497DAA19211EEdff47f25384cdc3", "base_token": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"},
            {"name": "WETH", "comet": "0xA17581A9E3356d9A858b789D68B4d866e593aE94", "base_token": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"},
            {"name": "USDT", "comet": "0x3Afdc9BCA9213A35503b077a6072F3D0d5AB0840", "base_token": "0xdAC17F958D2ee523a2206206994597C13D831ec7"},
            {"name": "WBTC", "comet": "0xe85Dc543813B8c2CFEaAc371517b925a166a9293", "base_token": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599"},
        ],
        "base": [
            {"name": "USDC", "comet": "0xb125E6687d4313864e53df431d5425969c15Eb2F", "base_token": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"},
            {"name": "WETH", "comet": "0x46e6b214b524310239732D51387075E0e70970bf", "base_token": "0x4200000000000000000000000000000000000006"},
            {"name": "AERO", "comet": "0x784efeB622244d2348d4F2522f8860B96fbEcE89", "base_token": "0x940181a94A35A4569E4529A3CDfB74e38FD98631"},
        ],
        "arbitrum": [
            {"name": "USDC", "comet": "0x9c4ec768c28520B50860ea7a15bd7213a9fF58bf", "base_token": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831"},
            {"name": "USDC.e", "comet": "0xA5EDBDD9646f8dFF606d7448e414884C7d905dCA", "base_token": "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8"},
            {"name": "USDT", "comet": "0xd98Be00b5D27fc98112BdE293e487f8D4cA57d07", "base_token": "0xFd086bC7CD5C481DCC9C85ebe478A1C0b69FCbb9"},
            {"name": "WETH", "comet": "0x6f7D514bbD4aFf3BcD1140B7344b32f063dEe486", "base_token": "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1"},
        ],
        "optimism": [
            {"name": "USDC", "comet": "0x2e44e174f7D53F0212823acC11C01A11d58c5bCB", "base_token": "0x0b2C639c533813f4Aa9D7837CAf62653d097Ff85"},
            {"name": "USDT", "comet": "0x995E394b8B2437aC8Ce61Ee0bC610D617962B214", "base_token": "0x94b008aD8e49A1b7b13E05e6f9eF0dCff6CEeF8"},
            {"name": "WETH", "comet": "0xE36A30D249f7761327fd973001A32010b521b6Fd", "base_token": "0x4200000000000000000000000000000000000006"},
        ],
        "polygon": [
            {"name": "USDC", "comet": "0xF25212E676D1F7F89Cd72fFEe66158f541246445", "base_token": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"},
            {"name": "USDT", "comet": "0xaeB318360f27748Acb200CE616E389A6C9409a07", "base_token": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F"},
        ],
    }
    _compound_selectors = {
        "balance_of": "0x70a08231",
        "borrow_balance_of": "0x374c49b4",
    }
    _uniswap_v3_position_managers = {
        "ethereum": "0xC36442b4a4522E871399CD717aBDD847Ab11FE88",
        "arbitrum": "0xC36442b4a4522E871399CD717aBDD847Ab11FE88",
        "optimism": "0xC36442b4a4522E871399CD717aBDD847Ab11FE88",
        "polygon": "0xC36442b4a4522E871399CD717aBDD847Ab11FE88",
        "base": "0x03a520b32C04BF3bEEf7BEb72E919cf822Ed34f1",
    }
    _uniswap_selectors = {"positions": "0x99fbab88"}

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

    def _fetch_blockscout_nfts(self, wallet: str, network: str) -> List[Dict[str, Any]]:
        base_url = self._blockscout.get(network)
        if not base_url:
            return []
        url = base_url.split("/api/v2/")[0] + "/api/v2/addresses/{wallet}/nft"
        try:
            response = requests.get(url.format(wallet=wallet), timeout=20, headers={"accept": "application/json"})
            response.raise_for_status()
            return response.json().get("items") or []
        except Exception:
            return []

    def _fetch_rpc_native_balance(self, wallet: str, network: str) -> float:
        rpc_urls = self._public_rpc_fallbacks.get(network) or ([self._public_rpc[network]] if network in self._public_rpc else [])
        if not rpc_urls:
            raise AdapterError(f"Sem RPC público configurado para {network}.")
        payload = {"jsonrpc": "2.0", "method": "eth_getBalance", "params": [wallet, "latest"], "id": 1}
        last_error: Exception | None = None
        for rpc in rpc_urls:
            try:
                response = requests.post(rpc, json=payload, timeout=20)
                response.raise_for_status()
                data = response.json()
                if data.get("error"):
                    raise AdapterError(f"Erro RPC {network}: {data['error']}")
                raw = data.get("result")
                return int(raw, 16) / 1e18 if raw else 0.0
            except Exception as exc:
                last_error = exc
                continue
        raise AdapterError(f"Falha ao consultar RPC {network}: {last_error}")

    def _eth_call(self, network: str, to: str, data: str) -> str | None:
        rpc_urls = self._public_rpc_fallbacks.get(network) or ([self._public_rpc[network]] if network in self._public_rpc else [])
        if not rpc_urls:
            return None
        for rpc in rpc_urls:
            try:
                response = requests.post(
                    rpc,
                    json={"jsonrpc": "2.0", "method": "eth_call", "params": [{"to": to, "data": data}, "latest"], "id": 1},
                    timeout=20,
                )
                response.raise_for_status()
                payload = response.json()
                if payload.get("error"):
                    continue
                result = payload.get("result")
                if isinstance(result, str) and result.startswith("0x"):
                    return result
            except Exception:
                continue
        return None

    @staticmethod
    def _encode_address(address: str) -> str:
        return address.lower().replace("0x", "").rjust(64, "0")

    @staticmethod
    def _decode_words(result: str | None) -> List[str]:
        if not result or result == "0x":
            return []
        body = result[2:]
        return [body[i : i + 64] for i in range(0, len(body), 64) if len(body[i : i + 64]) == 64]

    @staticmethod
    def _word_to_int(word: str, signed: bool = False) -> int:
        value = int(word, 16)
        if signed and value >= 2**255:
            value -= 2**256
        return value

    @staticmethod
    def _word_to_address(word: str) -> str:
        return "0x" + word[-40:]

    @staticmethod
    def _decode_abi_string_at(words: List[str], idx: int) -> str | None:
        try:
            length = int(words[idx], 16)
            raw = "".join(words[idx + 1 : idx + 1 + ((length + 31) // 32)])
            return bytes.fromhex(raw[: length * 2]).decode("utf-8", errors="ignore").strip("\x00")
        except Exception:
            return None

    def _decode_aave_reserves(self, result: str | None) -> List[Dict[str, str]]:
        words = self._decode_words(result)
        if len(words) < 3:
            return []
        try:
            count = int(words[1], 16)
        except Exception:
            return []
        reserves: List[Dict[str, str]] = []
        # getAllReservesTokens() returns tuple(string symbol, address tokenAddress)[];
        # array item offsets are relative to the first offset word (word index 2).
        for i in range(count):
            try:
                offset_words = int(words[2 + i], 16) // 32
                tuple_idx = 2 + offset_words
                symbol_offset_words = int(words[tuple_idx], 16) // 32
                address = self._word_to_address(words[tuple_idx + 1])
                symbol = self._decode_abi_string_at(words, tuple_idx + symbol_offset_words) or "?"
            except Exception:
                continue
            reserves.append({"symbol": symbol, "address": address})
        return reserves

    def _erc20_decimals(self, network: str, token: str) -> int:
        words = self._decode_words(self._eth_call(network, token, self._aave_selectors["decimals"]))
        if not words:
            return 18
        try:
            return int(words[0], 16)
        except Exception:
            return 18

    def _erc20_symbol(self, network: str, token: str) -> str | None:
        words = self._decode_words(self._eth_call(network, token, self._aave_selectors["symbol"]))
        if not words:
            return None
        # Standard dynamic string.
        try:
            if int(words[0], 16) == 32 and len(words) >= 3:
                return self._decode_abi_string_at(words, 2)
        except Exception:
            pass
        # bytes32-style symbol fallback.
        try:
            return bytes.fromhex(words[0]).decode("utf-8", errors="ignore").strip("\x00") or None
        except Exception:
            return None

    def _aave_v3_positions(self, wallet: str, network: str) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
        market = self._aave_v3_markets.get(network)
        if not market:
            return [], {"enabled": False, "reason": "Aave V3 sem mapping para esta rede."}
        reserves = self._decode_aave_reserves(
            self._eth_call(network, market["data_provider"], self._aave_selectors["get_all_reserves_tokens"])
        )
        if not reserves:
            return [], {"enabled": True, "protocol": "Aave V3", "error": "Não foi possível listar reservas via RPC público."}

        positions: List[Dict[str, Any]] = []
        raw_positions: List[Dict[str, Any]] = []
        for reserve in reserves[:60]:
            token = reserve.get("address")
            if not token:
                continue
            data = (
                self._aave_selectors["get_user_reserve_data"]
                + self._encode_address(token)
                + self._encode_address(wallet)
            )
            words = self._decode_words(self._eth_call(network, market["data_provider"], data))
            if len(words) < 3:
                continue
            try:
                supplied_raw = int(words[0], 16)
                stable_debt_raw = int(words[1], 16)
                variable_debt_raw = int(words[2], 16)
            except Exception:
                continue
            if supplied_raw <= 0 and stable_debt_raw <= 0 and variable_debt_raw <= 0:
                continue
            decimals = self._erc20_decimals(network, token)
            symbol = reserve.get("symbol") or self._erc20_symbol(network, token) or "?"
            supplied = supplied_raw / (10**decimals)
            debt = (stable_debt_raw + variable_debt_raw) / (10**decimals)
            dex_data = self._fetch_dexscreener_token(token, network)
            price = dex_data.get("price_usd")
            supplied_usd = supplied * price if price is not None else None
            debt_usd = debt * price if price is not None else None
            net_usd = (supplied_usd or 0) - (debt_usd or 0) if price is not None else None
            raw_positions.append(
                {
                    "symbol": symbol,
                    "token": token,
                    "supplied": supplied,
                    "debt": debt,
                    "price_usd": price,
                    "net_usd": net_usd,
                }
            )
            # Keep the main report clean: only render positions with reliable positive USD value.
            if net_usd is None or net_usd <= 0:
                continue
            positions.append(
                {
                    "name": f"Aave V3 {symbol}",
                    "size": f"supply {supplied:.8g} {symbol}" + (f" / debt {debt:.8g} {symbol}" if debt else ""),
                    "usd_value": self._fmt_usd(net_usd),
                    "change_24h": f"{dex_data.get('change_24h'):.2f}%" if isinstance(dex_data.get("change_24h"), (int, float)) else "n/d",
                    "protocol": "Aave V3",
                    "category": "defi-lending",
                    "asset_usd_value": self._fmt_usd(supplied_usd) if supplied_usd is not None else "n/d",
                    "debt_usd_value": self._fmt_usd(debt_usd) if debt_usd is not None else "n/d",
                    "contract": token,
                    "price_source": "Dexscreener" if price is not None else "n/d",
                }
            )
        return positions, {
            "enabled": True,
            "protocol": "Aave V3",
            "reserve_count": len(reserves),
            "raw_positions": raw_positions,
            "source": "Aave V3 contratos via RPC público + Dexscreener para preço",
        }

    def _compound_v3_positions(self, wallet: str, network: str) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
        markets = self._compound_v3_markets.get(network) or []
        if not markets:
            return [], {"enabled": False, "reason": "Compound V3 sem mapping para esta rede."}
        positions: List[Dict[str, Any]] = []
        raw_positions: List[Dict[str, Any]] = []
        for market in markets:
            comet = market["comet"]
            base_token = market["base_token"]
            user_arg = self._encode_address(wallet)
            supply_words = self._decode_words(self._eth_call(network, comet, self._compound_selectors["balance_of"] + user_arg))
            borrow_words = self._decode_words(self._eth_call(network, comet, self._compound_selectors["borrow_balance_of"] + user_arg))
            if not supply_words and not borrow_words:
                continue
            supplied_raw = int(supply_words[0], 16) if supply_words else 0
            borrowed_raw = int(borrow_words[0], 16) if borrow_words else 0
            if supplied_raw <= 0 and borrowed_raw <= 0:
                continue
            decimals = self._erc20_decimals(network, base_token)
            symbol = self._erc20_symbol(network, base_token) or market.get("name") or "?"
            supplied = supplied_raw / (10**decimals)
            borrowed = borrowed_raw / (10**decimals)
            dex_data = self._fetch_dexscreener_token(base_token, network)
            price = dex_data.get("price_usd")
            supplied_usd = supplied * price if price is not None else None
            borrowed_usd = borrowed * price if price is not None else None
            net_usd = (supplied_usd or 0) - (borrowed_usd or 0) if price is not None else None
            raw_positions.append(
                {
                    "market": market.get("name"),
                    "comet": comet,
                    "base_token": base_token,
                    "symbol": symbol,
                    "supplied": supplied,
                    "borrowed": borrowed,
                    "price_usd": price,
                    "net_usd": net_usd,
                }
            )
            if net_usd is None or (supplied == 0 and borrowed == 0):
                continue
            positions.append(
                {
                    "name": f"Compound V3 {symbol}",
                    "size": f"supply {supplied:.8g} {symbol}" + (f" / borrow {borrowed:.8g} {symbol}" if borrowed else ""),
                    "usd_value": self._fmt_usd(net_usd),
                    "change_24h": f"{dex_data.get('change_24h'):.2f}%" if isinstance(dex_data.get("change_24h"), (int, float)) else "n/d",
                    "protocol": "Compound V3",
                    "category": "defi-lending",
                    "asset_usd_value": self._fmt_usd(supplied_usd) if supplied_usd is not None else "n/d",
                    "debt_usd_value": self._fmt_usd(borrowed_usd) if borrowed_usd is not None else "n/d",
                    "contract": comet,
                    "base_token": base_token,
                    "price_source": "Dexscreener" if price is not None else "n/d",
                }
            )
        return positions, {
            "enabled": True,
            "protocol": "Compound V3",
            "market_count": len(markets),
            "raw_positions": raw_positions,
            "source": "Compound V3 Comet contratos via RPC público + Dexscreener para preço",
        }

    def _uniswap_v3_lp_positions(self, wallet: str, network: str) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
        manager = self._uniswap_v3_position_managers.get(network)
        if not manager:
            return [], {"enabled": False, "reason": "Uniswap V3 Position Manager sem mapping para esta rede."}
        manager_lc = manager.lower()
        nfts = self._fetch_blockscout_nfts(wallet, network)
        raw_positions: List[Dict[str, Any]] = []
        for item in nfts[:100]:
            token = item.get("token") if isinstance(item.get("token"), dict) else {}
            contract = str(token.get("address_hash") or "").lower()
            token_id = item.get("id") or item.get("token_id")
            if contract != manager_lc or token_id in {None, ""}:
                continue
            try:
                token_id_int = int(str(token_id), 10)
            except Exception:
                continue
            data = self._uniswap_selectors["positions"] + hex(token_id_int)[2:].rjust(64, "0")
            words = self._decode_words(self._eth_call(network, manager, data))
            if len(words) < 12:
                raw_positions.append({"token_id": token_id, "contract": manager, "error": "positions() sem retorno decodificável"})
                continue
            token0 = self._word_to_address(words[2])
            token1 = self._word_to_address(words[3])
            fee = self._word_to_int(words[4])
            tick_lower = self._word_to_int(words[5], signed=True)
            tick_upper = self._word_to_int(words[6], signed=True)
            liquidity = self._word_to_int(words[7])
            raw_positions.append(
                {
                    "token_id": str(token_id),
                    "contract": manager,
                    "token0": token0,
                    "token1": token1,
                    "symbol0": self._erc20_symbol(network, token0),
                    "symbol1": self._erc20_symbol(network, token1),
                    "fee": fee,
                    "tick_lower": tick_lower,
                    "tick_upper": tick_upper,
                    "liquidity": liquidity,
                    "tokens_owed0_raw": self._word_to_int(words[10]),
                    "tokens_owed1_raw": self._word_to_int(words[11]),
                }
            )
        # Do not render LP value in main output yet: exact valuation needs pool slot0/tick math.
        return [], {
            "enabled": True,
            "protocol": "Uniswap V3 LP",
            "position_manager": manager,
            "nft_count_scanned": len(nfts),
            "raw_positions": raw_positions,
            "source": "Blockscout NFTs + Uniswap V3 NonfungiblePositionManager.positions via RPC público",
            "limit": "Detecção 0-key implementada; valuation exata de liquidez ainda não entra no total para evitar número falso.",
        }

    def _fetch_dexscreener_token(self, contract: str | None, network: str) -> Dict[str, Any]:
        if not contract:
            return {}
        chain_map = {"bnb": "bsc"}
        chain_id = chain_map.get(network, network)
        try:
            response = requests.get(
                self._dexscreener_token_url.format(contract=contract),
                timeout=15,
            )
            response.raise_for_status()
            pairs = response.json().get("pairs") or []
        except Exception:
            return {}

        def liquidity_usd(pair: Dict[str, Any]) -> float:
            liquidity = pair.get("liquidity") if isinstance(pair.get("liquidity"), dict) else {}
            try:
                return float(liquidity.get("usd") or 0)
            except Exception:
                return 0.0

        contract_lc = contract.lower()
        matching = []
        for pair in pairs:
            if pair.get("chainId") != chain_id:
                continue
            base_token = pair.get("baseToken") if isinstance(pair.get("baseToken"), dict) else {}
            # Dexscreener priceUsd is quoted for baseToken. Avoid using pairs where
            # the requested contract appears only as quoteToken, or we may price the
            # wrong asset (common in WETH/USDC pools).
            if str(base_token.get("address") or "").lower() == contract_lc:
                matching.append(pair)
        if not matching:
            return {}
        best = max(matching, key=liquidity_usd)
        try:
            price_usd = float(best.get("priceUsd")) if best.get("priceUsd") not in {None, ""} else None
        except Exception:
            price_usd = None
        price_change = best.get("priceChange") if isinstance(best.get("priceChange"), dict) else {}
        return {
            "price_usd": price_usd,
            "change_24h": price_change.get("h24"),
            "liquidity_usd": liquidity_usd(best),
            "dex": best.get("dexId"),
            "pair_url": best.get("url"),
            "pair_address": best.get("pairAddress"),
        }

    def _fetch_debank_defi_positions(self, wallet: str, network: str) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
        access_key = os.environ.get("DEBANK_ACCESS_KEY") or os.environ.get("DEBANK_API_KEY")
        chain_id = self._debank_chain_ids.get(network)
        if not access_key or not chain_id:
            return [], {"enabled": False, "reason": "DEBANK_ACCESS_KEY ausente ou rede sem mapping."}
        try:
            response = requests.get(
                self._debank_complex_protocols_url,
                params={"id": wallet, "chain_id": chain_id},
                headers={"accept": "application/json", "AccessKey": access_key},
                timeout=25,
            )
            response.raise_for_status()
            protocols = response.json() or []
        except Exception as exc:
            return [], {"enabled": True, "error": str(exc)}

        positions: List[Dict[str, Any]] = []
        for protocol in protocols if isinstance(protocols, list) else []:
            if not isinstance(protocol, dict):
                continue
            for item in protocol.get("portfolio_item_list") or []:
                stats = item.get("stats") if isinstance(item.get("stats"), dict) else {}
                net_usd = stats.get("net_usd_value")
                try:
                    net_value = float(net_usd or 0)
                except Exception:
                    net_value = 0.0
                if net_value <= 0:
                    continue
                positions.append(
                    {
                        "name": f"{protocol.get('name') or protocol.get('id')}: {item.get('name') or 'DeFi'}",
                        "size": "n/d",
                        "usd_value": self._fmt_usd(net_value),
                        "change_24h": "n/d",
                        "protocol": protocol.get("name") or protocol.get("id"),
                        "protocol_id": protocol.get("id"),
                        "chain": protocol.get("chain") or chain_id,
                        "category": "defi",
                        "asset_usd_value": self._fmt_usd(self._safe_float(stats.get("asset_usd_value"))),
                        "debt_usd_value": self._fmt_usd(self._safe_float(stats.get("debt_usd_value"))),
                    }
                )
        return positions, {"enabled": True, "chain_id": chain_id, "protocol_count": len(protocols), "raw_protocols": protocols}

    @staticmethod
    def _safe_float(value: Any) -> float | None:
        try:
            if value in {None, "", "n/d"}:
                return None
            return float(value)
        except Exception:
            return None

    @staticmethod
    def _parse_brl_number(value: Any) -> float:
        try:
            return float(str(value or "0").replace(".", "").replace(",", "."))
        except Exception:
            return 0.0

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
        suspicious_tokens: List[Dict[str, Any]] = []
        filtered_tokens: List[Dict[str, Any]] = []
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
            name = info.get("name") or ""
            contract = info.get("address") or info.get("contract") or info.get("id")
            decision = classify_token(name=name, symbol=symbol, usd_value=usd_value)
            if not decision.visible:
                payload = audit_payload(
                    symbol=symbol,
                    name=name,
                    amount=round(amount, 8),
                    contract=contract,
                    reason=decision.reason or "Token ocultado do output principal.",
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
                    "amount": round(amount, 8),
                    "usd_value": self._fmt_usd(usd_value) if usd_value is not None else "n/d",
                    "change_24h": f"{price_info.get('diff')}%" if isinstance(price_info, dict) and price_info.get("diff") is not None else "n/d",
                    "category": decision.category,
                    "contract": contract,
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
        hidden_count = len(suspicious_tokens) + len(filtered_tokens)
        if hidden_count:
            insights.append(f"🛡️ {hidden_count} token(s) ocultado(s) do output principal por segurança/baixo valor.")
        aave_positions, aave_raw = self._aave_v3_positions(wallet, network)
        compound_positions, compound_raw = self._compound_v3_positions(wallet, network)
        uniswap_positions, uniswap_raw = self._uniswap_v3_lp_positions(wallet, network)
        defi_positions = aave_positions + compound_positions + uniswap_positions
        for position in defi_positions:
            total_usd += self._parse_brl_number(position.get("usd_value"))
        if aave_positions:
            insights.append(f"🏦 {len(aave_positions)} posição(ões) Aave V3 detectada(s) via RPC público.")
        if compound_positions:
            insights.append(f"🏦 {len(compound_positions)} posição(ões) Compound V3 detectada(s) via RPC público.")
        uni_raw_positions = uniswap_raw.get("raw_positions") if isinstance(uniswap_raw, dict) else []
        if uni_raw_positions:
            insights.append(f"🦄 {len(uni_raw_positions)} NFT(s) de liquidez Uniswap V3 detectado(s); valuation mantida fora do total até cálculo exato de liquidez.")

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
            positions=defi_positions,
            insights=insights or ["ℹ️ Snapshot obtido com fonte pública Ethereum."],
            actions=[
                "Revisar ativos sem preço em USD, se existirem.",
                "Adicionar fonte complementar para posições/DeFi e cobertura multi-EVM mais profunda.",
            ],
            coverage=Coverage(
                level="medium",
                summary="Ethereum com saldo/tokens via fonte pública e DeFi 0-key para Aave V3/Compound V3; Uniswap V3 LP é detectado sem valuation no total.",
                sources=["Ethplorer freekey (Ethereum)", "RPC público Ethereum", "Aave V3 contratos públicos", "Compound V3 Comet público", "Uniswap V3 Position Manager público"],
                limits=[
                    "Esta integração real inicial está validada para Ethereum.",
                    "Uniswap V3 LP tem detecção implementada, mas valuation de liquidez ainda não entra no total.",
                    "Tokens suspeitos são ocultados do output principal e preservados em raw.suspicious_tokens.",
                    "Tokens sem preço confiável ou abaixo de $0.01 são ocultados e preservados em raw.filtered_tokens.",
                ],
            ),
            raw={
                "wallet": wallet,
                "network": network,
                "ethplorer": payload,
                "defi": {"aave_v3": aave_raw, "compound_v3": compound_raw, "uniswap_v3_lp": uniswap_raw},
                "suspicious_tokens": suspicious_tokens,
                "filtered_tokens": filtered_tokens,
            },
        )

    def collect(self, wallet: str, network: str) -> PortfolioResult:
        network = network.lower()
        if network == "ethereum":
            try:
                payload = self._fetch_ethplorer(wallet)
                return self._build_from_ethplorer(wallet, network, payload)
            except AdapterError:
                # Ethplorer freekey occasionally returns 502/Bad Gateway. Fall back
                # to the generic public-RPC + Blockscout path instead of failing
                # the whole daily report.
                pass

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
        defi_positions, aave_raw = self._aave_v3_positions(wallet, network)
        compound_positions, compound_raw = self._compound_v3_positions(wallet, network)
        defi_positions.extend(compound_positions)
        uniswap_positions, uniswap_raw = self._uniswap_v3_lp_positions(wallet, network)
        defi_positions.extend(uniswap_positions)
        debank_positions: List[Dict[str, Any]] = []
        debank_raw: Dict[str, Any] = {"enabled": False, "reason": "DeBank opcional; desativado sem chave no ambiente."}
        if os.environ.get("DEBANK_ACCESS_KEY") or os.environ.get("DEBANK_API_KEY"):
            debank_positions, debank_raw = self._fetch_debank_defi_positions(wallet, network)
            defi_positions.extend(debank_positions)
        for position in defi_positions:
            total_usd += self._parse_brl_number(position.get("usd_value"))
        suspicious_tokens: List[Dict[str, Any]] = []
        filtered_tokens: List[Dict[str, Any]] = []
        for item in token_items[:20]:
            token = item.get("token") or {}
            symbol = token.get("symbol") or "?"
            name = token.get("name") or ""
            decimals = int(token.get("decimals") or 0)
            raw_value = int(item.get("value") or 0)
            amount = raw_value / (10 ** decimals) if decimals >= 0 else 0
            contract = token.get("address_hash")
            exchange_rate = token.get("exchange_rate")
            try:
                price = float(exchange_rate) if exchange_rate not in {None, ""} else None
            except Exception:
                price = None
            dex_data = self._fetch_dexscreener_token(contract, network) if network in {"base", "arbitrum"} else {}
            price_source = "Blockscout"
            if price is None and dex_data.get("price_usd") is not None:
                price = dex_data.get("price_usd")
                price_source = "Dexscreener"
            elif dex_data:
                price_source = "Blockscout+Dexscreener"
            usd_value = amount * price if price is not None else None
            decision = classify_token(name=name, symbol=symbol, usd_value=usd_value)
            if not decision.visible:
                payload = audit_payload(
                    symbol=symbol,
                    name=name,
                    amount=round(amount, 8),
                    contract=contract,
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
                    "change_24h": f"{dex_data.get('change_24h'):.2f}%" if isinstance(dex_data.get("change_24h"), (int, float)) else "n/d",
                    "category": category,
                    "contract": contract,
                    "liquidity_usd": dex_data.get("liquidity_usd"),
                    "price_source": price_source,
                    "dex": dex_data.get("dex"),
                    "pair_url": dex_data.get("pair_url"),
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
        if defi_positions:
            aave_count = len([p for p in defi_positions if p.get("protocol") == "Aave V3"])
            compound_count = len([p for p in defi_positions if p.get("protocol") == "Compound V3"])
            if aave_count:
                insights.append(f"🏦 {aave_count} posição(ões) Aave V3 detectada(s) via RPC público em {network}.")
            if compound_count:
                insights.append(f"🏦 {compound_count} posição(ões) Compound V3 detectada(s) via RPC público em {network}.")
            if debank_positions:
                insights.append(f"🏦 {len(debank_positions)} posição(ões) DeFi extra detectada(s) via DeBank opcional em {network}.")
        else:
            insights.append("🏦 DeFi EVM 0-key ativo para Aave V3, Compound V3 e detecção Uniswap V3 LP.")
        uni_raw_positions = uniswap_raw.get("raw_positions") if isinstance(uniswap_raw, dict) else []
        if uni_raw_positions:
            insights.append(f"🦄 {len(uni_raw_positions)} NFT(s) de liquidez Uniswap V3 detectado(s); valuation mantida fora do total até cálculo exato de liquidez.")
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
            positions=defi_positions,
            insights=insights,
            actions=[
                "Para DeFi mais amplo, priorizar módulos 0-key por protocolo antes de recorrer a APIs pagas.",
                "Validar tokens de baixa liquidez antes de usar em decisão operacional.",
            ],
            coverage=Coverage(
                level="medium",
                summary="Saldo nativo, tokens ERC-20, Aave V3 e Compound V3 via fontes públicas; Uniswap V3 LP é detectado sem key e fica fora do total até valuation exata; DeBank permanece opcional.",
                sources=[f"RPC público {network}", "CoinGecko público", "Blockscout público", "Dexscreener público", "Aave V3 contratos públicos", "Compound V3 Comet público", "Uniswap V3 Position Manager público", "DeBank opcional"],
                limits=[
                    "Preço/24h por token depende da cobertura do Blockscout/Coingecko/Dexscreener e de liquidez pública.",
                    "DeFi 0-key cobre Aave V3 e Compound V3 nesta fase; Uniswap V3 LP tem detecção implementada, mas valuation de liquidez ainda não entra no total.",
                    "Posições DeFi universais ainda exigem indexador opcional como DeBank; sem fonte confiável, a skill não inventa posições.",
                    "Tokens suspeitos são ocultados do output principal e preservados em raw.suspicious_tokens.",
                    "Tokens sem preço confiável ou abaixo de $0.01 são ocultados e preservados em raw.filtered_tokens.",
                ],
            ),
            raw={
                "wallet": wallet,
                "network": network,
                "native_balance": native_balance,
                "blockscout_tokens": token_items,
                "defi": {"aave_v3": aave_raw, "compound_v3": compound_raw, "uniswap_v3_lp": uniswap_raw, "debank_optional": debank_raw},
                "suspicious_tokens": suspicious_tokens,
                "filtered_tokens": filtered_tokens,
            },
        )
