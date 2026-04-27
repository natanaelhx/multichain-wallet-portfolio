from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Coverage:
    level: str
    summary: str
    sources: List[str] = field(default_factory=list)
    limits: List[str] = field(default_factory=list)


@dataclass
class PortfolioResult:
    ok: bool
    network: str
    wallet_input: str
    wallet_resolved: str
    adapter: str
    summary: Dict[str, Any]
    balances: List[Dict[str, Any]] = field(default_factory=list)
    positions: List[Dict[str, Any]] = field(default_factory=list)
    orders: List[Dict[str, Any]] = field(default_factory=list)
    nft_summary: Optional[Dict[str, Any]] = None
    insights: List[str] = field(default_factory=list)
    actions: List[str] = field(default_factory=list)
    coverage: Coverage = field(default_factory=lambda: Coverage(level="low", summary="Sem cobertura."))
    raw: Dict[str, Any] = field(default_factory=dict)


class AdapterError(RuntimeError):
    pass


class BaseAdapter:
    name = "base"

    def supports(self, network: str) -> bool:
        raise NotImplementedError

    def collect(self, wallet: str, network: str) -> PortfolioResult:
        raise NotImplementedError
