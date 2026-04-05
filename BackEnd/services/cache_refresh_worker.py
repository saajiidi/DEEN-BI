"""Detached worker that refreshes WooCommerce cache files without blocking the UI."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
os.chdir(ROOT_DIR)

from BackEnd.services.hybrid_data_loader import (  # noqa: E402
    refresh_woocommerce_orders_cache,
    refresh_woocommerce_stock_cache,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Refresh local WooCommerce cache in the background.")
    parser.add_argument("kind", choices=["orders", "stock", "full_history"])
    parser.add_argument("--start-date")
    parser.add_argument("--end-date")
    parser.add_argument("--days", type=int, default=30)
    args = parser.parse_args()

    if args.kind == "orders":
        refresh_woocommerce_orders_cache(
            days=args.days,
            start_date=args.start_date,
            end_date=args.end_date,
        )
    elif args.kind == "full_history":
        refresh_woocommerce_orders_cache(
            days=args.days,
            start_date=None,
            end_date=args.end_date,
            full_sync=True,
        )
    else:
        refresh_woocommerce_stock_cache()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
