import unittest
from unittest.mock import patch
from pathlib import Path
import tempfile

import pandas as pd

from BackEnd.services import hybrid_data_loader


class _FakeWooService:
    def __init__(self):
        self.calls = []

    def fetch_all_historical_orders(self, after=None, before=None, status="any", show_progress=True, show_errors=True):
        self.calls.append({"after": after, "before": before, "status": status})
        return pd.DataFrame(
            {
                "Order Number": ["1001"],
                "Order Date": ["2026-04-01 10:00:00"],
                "Customer Name": ["Jane"],
                "Qty": [1],
                "Item Name": ["Polo"],
                "Order Total Amount": [1200],
                "_source": ["woocommerce_api"],
            }
        )

    def get_stock_report(self, show_errors=True):
        return pd.DataFrame(
            {
                "ID": [1],
                "Name": ["Polo"],
                "SKU": ["POLO-1"],
                "Stock Status": ["instock"],
                "Stock Quantity": ["7"],
                "Price": ["1200"],
            }
        )


class _FakeResponse:
    def __init__(self, csv_text: str):
        self.content = csv_text.encode("utf-8")

    def raise_for_status(self):
        return None


class TestHybridDataLoader(unittest.TestCase):
    def setUp(self):
        hybrid_data_loader.load_woocommerce_live_data.clear()
        hybrid_data_loader.load_woocommerce_stock_data.clear()
        hybrid_data_loader.load_live_stream_data.clear()
        hybrid_data_loader.load_comparison_data.clear()

    def test_woocommerce_loader_respects_selected_date_range(self):
        fake_service = _FakeWooService()

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            with (
                patch.object(hybrid_data_loader, "_cache_file", side_effect=lambda name: cache_dir / name),
                patch.object(
                    hybrid_data_loader.st,
                    "secrets",
                    {
                        "woocommerce": {
                            "store_url": "https://example.com",
                            "consumer_key": "ck_test",
                            "consumer_secret": "cs_test",
                        }
                    },
                ),
                patch("BackEnd.services.woocommerce_service.WooCommerceService", return_value=fake_service),
            ):
                df = hybrid_data_loader.load_woocommerce_live_data(
                    start_date="2026-04-01",
                    end_date="2026-04-05",
                )

        self.assertFalse(df.empty)
        self.assertEqual(len(fake_service.calls), 1)
        self.assertEqual(fake_service.calls[0]["after"], "2026-04-01T00:00:00Z")
        self.assertEqual(fake_service.calls[0]["before"], "2026-04-05T23:59:59Z")

    def test_woocommerce_stock_loader_uses_api_and_normalizes_numbers(self):
        fake_service = _FakeWooService()

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            with (
                patch.object(hybrid_data_loader, "_cache_file", side_effect=lambda name: cache_dir / name),
                patch.object(
                    hybrid_data_loader.st,
                    "secrets",
                    {
                        "woocommerce": {
                            "store_url": "https://example.com",
                            "consumer_key": "ck_test",
                            "consumer_secret": "cs_test",
                        }
                    },
                ),
                patch("BackEnd.services.woocommerce_service.WooCommerceService", return_value=fake_service),
            ):
                df = hybrid_data_loader.load_woocommerce_stock_data()

        self.assertEqual(len(df), 1)
        self.assertEqual(float(df.loc[0, "Stock Quantity"]), 7.0)
        self.assertEqual(float(df.loc[0, "Price"]), 1200.0)
        self.assertEqual(df.loc[0, "_source"], "woocommerce_stock_api")

    def test_live_stream_loader_uses_locked_stream_url(self):
        csv_text = "Order Number,Order Date,Customer Name,Qty,Item Name,Order Total Amount\n1001,2026-04-05 10:00:00,Jane,2,Polo,2400\n"

        with patch("BackEnd.services.hybrid_data_loader.requests.get", return_value=_FakeResponse(csv_text)) as mock_get:
            df = hybrid_data_loader.load_live_stream_data()

        self.assertFalse(df.empty)
        self.assertEqual(mock_get.call_args.args[0], hybrid_data_loader.LIVE_STREAM_URL)

    def test_comparison_loader_uses_locked_comparison_url(self):
        csv_text = "Order Number,Order Date,Customer Name,Qty,Item Name,Order Total Amount\n1000,2026-04-04 10:00:00,Jane,1,Polo,1200\n"

        with patch("BackEnd.services.hybrid_data_loader.requests.get", return_value=_FakeResponse(csv_text)) as mock_get:
            df = hybrid_data_loader.load_comparison_data()

        self.assertFalse(df.empty)
        self.assertEqual(mock_get.call_args.args[0], hybrid_data_loader.COMPARISON_SHEET_URL)

    def test_woocommerce_loader_uses_local_cache_when_range_is_covered(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            cached_df = pd.DataFrame(
                {
                    "order_id": ["1001"],
                    "order_date": ["2026-04-02 10:00:00"],
                    "customer_key": ["cust_1"],
                    "order_total": [1200],
                    "qty": [1],
                    "order_item_key": ["1001::polo"],
                    "source": ["woocommerce_api"],
                }
            )
            cached_df.to_parquet(cache_dir / "woo_orders.parquet", index=False)
            (cache_dir / "woo_orders_meta.json").write_text(
                """
                {
                  "cached_start": "2026-04-01 00:00:00",
                  "cached_end": "2026-04-05 23:59:59",
                  "fetched_at": "2099-04-05 12:00:00"
                }
                """,
                encoding="utf-8",
            )

            with (
                patch.object(hybrid_data_loader, "_cache_file", side_effect=lambda name: cache_dir / name),
                patch.object(
                    hybrid_data_loader,
                    "get_woocommerce_credentials",
                    return_value={
                        "store_url": "https://example.com",
                        "consumer_key": "ck_test",
                        "consumer_secret": "cs_test",
                    },
                ),
                patch("BackEnd.services.woocommerce_service.WooCommerceService") as mock_service,
            ):
                df = hybrid_data_loader.load_woocommerce_live_data(
                    start_date="2026-04-01",
                    end_date="2026-04-05",
                )

            self.assertFalse(df.empty)
            self.assertEqual(len(df), 1)
            mock_service.assert_not_called()

    def test_orders_cache_status_reports_fresh_local_snapshot(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            pd.DataFrame(
                {
                    "order_id": ["1001"],
                    "order_date": ["2026-04-02 10:00:00"],
                    "customer_key": ["cust_1"],
                    "order_total": [1200],
                    "qty": [1],
                    "order_item_key": ["1001::polo"],
                    "source": ["woocommerce_api"],
                }
            ).to_parquet(cache_dir / "woo_orders.parquet", index=False)
            (cache_dir / "woo_orders_meta.json").write_text(
                """
                {
                  "cached_start": "2026-04-01 00:00:00",
                  "cached_end": "2026-04-05 23:59:59",
                  "fetched_at": "2099-04-05 12:00:00"
                }
                """,
                encoding="utf-8",
            )

            with patch.object(hybrid_data_loader, "_cache_file", side_effect=lambda name: cache_dir / name):
                status = hybrid_data_loader.get_woocommerce_orders_cache_status(
                    start_date="2026-04-01",
                    end_date="2026-04-05",
                )

            self.assertTrue(status["cache_exists"])
            self.assertTrue(status["is_covered"])
            self.assertTrue(status["is_fresh"])
            self.assertFalse(status["needs_refresh"])

    def test_start_orders_background_refresh_spawns_worker_when_needed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            with (
                patch.object(hybrid_data_loader, "_cache_file", side_effect=lambda name: cache_dir / name),
                patch.object(
                    hybrid_data_loader,
                    "get_woocommerce_credentials",
                    return_value={
                        "store_url": "https://example.com",
                        "consumer_key": "ck_test",
                        "consumer_secret": "cs_test",
                    },
                ),
                patch.object(
                    hybrid_data_loader,
                    "get_woocommerce_orders_cache_status",
                    return_value={"is_running": False, "needs_refresh": True},
                ),
                patch.object(hybrid_data_loader, "_spawn_refresh_worker", return_value=True) as mock_spawn,
            ):
                started = hybrid_data_loader.start_orders_background_refresh(
                    start_date="2026-04-01",
                    end_date="2026-04-05",
                )

            self.assertTrue(started)
            mock_spawn.assert_called_once()
            self.assertTrue((cache_dir / "orders_refresh.lock").exists())

    def test_start_full_history_background_refresh_spawns_worker_when_needed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            with (
                patch.object(hybrid_data_loader, "_cache_file", side_effect=lambda name: cache_dir / name),
                patch.object(
                    hybrid_data_loader,
                    "get_woocommerce_credentials",
                    return_value={
                        "store_url": "https://example.com",
                        "consumer_key": "ck_test",
                        "consumer_secret": "cs_test",
                    },
                ),
                patch.object(
                    hybrid_data_loader,
                    "get_woocommerce_full_history_status",
                    return_value={"is_running": False, "needs_sync": True},
                ),
                patch.object(hybrid_data_loader, "_spawn_refresh_worker", return_value=True) as mock_spawn,
            ):
                started = hybrid_data_loader.start_full_history_background_refresh(
                    end_date="2026-04-05",
                )

            self.assertTrue(started)
            mock_spawn.assert_called_once()
            self.assertTrue((cache_dir / "full_history_refresh.lock").exists())


if __name__ == "__main__":
    unittest.main()
