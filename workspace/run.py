#!/usr/bin/env python3
"""Entry point operacional da skill multichain-wallet-portfolio."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from first_run_setup import build_first_run_payload
from normalizer import render_daily_summary, render_json, render_pretty, to_json_dict
from registry import resolve_adapter


def infer_network(wallet: str, explicit_network: str | None) -> str | None:
    if explicit_network:
        return explicit_network.strip().lower()
    raw = wallet.strip().lower()
    if raw.endswith('.eth') or raw.startswith('0x'):
        return 'ethereum'
    if raw.endswith('.sol') or len(raw) in range(32, 45):
        return 'solana'
    return None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Executor da skill multichain-wallet-portfolio')
    parser.add_argument('--mode', choices=['single', 'daily'], default='single')
    parser.add_argument('--wallet')
    parser.add_argument('--network')
    parser.add_argument('--evm-wallet')
    parser.add_argument('--solana-wallet')
    parser.add_argument('--wallets-file')
    parser.add_argument('--networks', default='ethereum,base,arbitrum,optimism,polygon,bnb,solana,hyperliquid')
    parser.add_argument('--format', choices=['pretty', 'json'], default='pretty')
    parser.add_argument('--first-run', action='store_true')
    parser.add_argument('--show-warnings', action='store_true', help='Mostra avisos técnicos de coleta em stderr.')
    return parser


def _load_wallets_file(path: str | None) -> dict:
    if not path:
        return {}
    try:
        return json.loads(Path(path).read_text(encoding='utf-8'))
    except FileNotFoundError as exc:
        raise SystemExit(f'Arquivo de wallets não encontrado: {path}') from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f'Arquivo de wallets inválido: {path}: {exc}') from exc


def _collect(wallet: str, network: str):
    adapter = resolve_adapter(network)
    if not adapter:
        raise SystemExit(f'Rede sem adapter operacional nesta v1 inicial: {network}')
    return adapter.collect(wallet, network)


def _wallet_for_network(network: str, args, config: dict) -> str | None:
    wallets = config.get('wallets') if isinstance(config.get('wallets'), dict) else config
    if network in {'solana'}:
        return args.solana_wallet or wallets.get('solana') or args.wallet
    if network in {'hyperliquid'}:
        return args.evm_wallet or wallets.get('hyperliquid') or wallets.get('evm') or args.wallet
    return args.evm_wallet or wallets.get('evm') or wallets.get(network) or args.wallet


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.first_run:
        payload = build_first_run_payload(wallet=args.wallet, network=args.network)
        print(render_json_dict(payload=args.format, payload_data=payload))
        return 0

    if args.mode == 'daily':
        config = _load_wallets_file(args.wallets_file)
        networks = [item.strip().lower() for item in args.networks.split(',') if item.strip()]
        results = []
        warnings = []
        for network in networks:
            wallet = _wallet_for_network(network, args, config)
            if not wallet:
                continue
            try:
                results.append(_collect(wallet, network))
            except Exception as exc:
                warning = f'falha ao coletar {network}: {exc}'
                warnings.append(warning)
                if args.show_warnings:
                    print(f'Aviso: {warning}', file=sys.stderr)
        if args.format == 'json':
            print(json.dumps({"ok": True, "mode": "daily", "warnings": warnings, "results": [to_json_dict(r) for r in results]}, ensure_ascii=False, indent=2))
        else:
            print(render_daily_summary(results))
        return 0

    if not args.wallet:
        raise SystemExit('Forneça --wallet.')

    network = infer_network(args.wallet, args.network)
    if not network:
        print(
            '{"ok": false, "reason": "Nao foi possivel detectar a rede automaticamente. Informe --network explicitamente."}'
        )
        return 2

    result = _collect(args.wallet, network)
    if args.format == 'json':
        print(render_json(result))
    else:
        print(render_pretty(result))
    return 0 if result.ok else 1


def render_json_dict(*, payload: str, payload_data: dict) -> str:
    import json

    return json.dumps(payload_data, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    sys.exit(main())
