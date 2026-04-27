from __future__ import annotations

from adapters.evm import EVMAdapter
from adapters.hyperliquid import HyperliquidAdapter
from adapters.solana import SolanaAdapter


def build_registry():
    return [
        EVMAdapter(),
        SolanaAdapter(),
        HyperliquidAdapter(),
    ]


def resolve_adapter(network: str):
    for adapter in build_registry():
        if adapter.supports(network):
            return adapter
    return None
