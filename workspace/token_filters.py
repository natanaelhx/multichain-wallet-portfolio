from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


STABLE_SYMBOLS = {"USDT", "USDC", "DAI", "FDUSD", "USDE", "PYUSD", "TUSD", "USDS"}
SUSPICIOUS_MARKERS = [
    "http://",
    "https://",
    "t.me",
    "telegram",
    "claim",
    "airdrop",
    "visit",
    "reward",
    "voucher",
    "bonus",
    "free",
    "✅",
    "🎁",
]
MIN_TOKEN_USD_VALUE = 0.01


@dataclass
class TokenDecision:
    visible: bool
    category: str
    reason: Optional[str] = None
    suspicious: bool = False
    low_value: bool = False


def is_stable(symbol: str) -> bool:
    return (symbol or "").upper() in STABLE_SYMBOLS


def is_suspicious_token(name: str, symbol: str) -> bool:
    text = f"{name or ''} {symbol or ''}".lower()
    return any(marker in text for marker in SUSPICIOUS_MARKERS)


def token_category(symbol: str, default: str = "outros") -> str:
    if is_stable(symbol):
        return "stablecoins"
    return default


def classify_token(*, name: str, symbol: str, usd_value: float | None) -> TokenDecision:
    category = token_category(symbol)
    if is_suspicious_token(name, symbol):
        return TokenDecision(
            visible=False,
            category=category,
            suspicious=True,
            reason="Token ocultado do output principal por marcador suspeito/link/claim.",
        )
    if usd_value is None:
        return TokenDecision(
            visible=False,
            category=category,
            low_value=True,
            reason="Token sem preço/valor USD confiável; ocultado do output principal.",
        )
    if usd_value < MIN_TOKEN_USD_VALUE:
        return TokenDecision(
            visible=False,
            category=category,
            low_value=True,
            reason=f"Token abaixo do valor mínimo de ${MIN_TOKEN_USD_VALUE:.2f}; ocultado do output principal.",
        )
    return TokenDecision(visible=True, category=category)


def audit_payload(*, symbol: str, name: str, amount: float, contract: str | None, reason: str, usd_value: str | None = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "symbol": symbol,
        "name": name,
        "amount": amount,
        "contract": contract,
        "reason": reason,
    }
    if usd_value is not None:
        payload["usd_value"] = usd_value
    return payload
