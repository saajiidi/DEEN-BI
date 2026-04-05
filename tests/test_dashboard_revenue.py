import unittest

import pandas as pd

from FrontEnd.pages.dashboard import _build_order_level_dataset, _estimate_line_revenue, _sum_order_level_revenue


class TestDashboardRevenue(unittest.TestCase):
    def test_order_level_revenue_counts_each_order_once(self):
        df = pd.DataFrame(
            {
                "Order Number": ["1001", "1001", "1002"],
                "Order Date": ["2026-04-01 10:00:00", "2026-04-01 10:00:00", "2026-04-02 11:00:00"],
                "Customer Name": ["Jane", "Jane", "John"],
                "Qty": [1, 2, 1],
                "Item Name": ["Polo", "Pant", "Cap"],
                "Order Total Amount": [1000, 1000, 500],
            }
        )

        order_df = _build_order_level_dataset(df)

        self.assertEqual(len(order_df), 2)
        self.assertEqual(_sum_order_level_revenue(df), 1500.0)

    def test_estimated_line_revenue_uses_item_cost_when_available(self):
        df = pd.DataFrame(
            {
                "Order Number": ["1001", "1001"],
                "Order Date": ["2026-04-01 10:00:00", "2026-04-01 10:00:00"],
                "Customer Name": ["Jane", "Jane"],
                "Qty": [1, 2],
                "Item Name": ["Polo", "Pant"],
                "Order Total Amount": [1000, 1000],
                "Item Cost": [400, 300],
            }
        )

        revenue = _estimate_line_revenue(df)

        self.assertEqual(list(revenue.round(2)), [400.0, 600.0])


if __name__ == "__main__":
    unittest.main()
