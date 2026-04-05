import unittest

import pandas as pd

from BackEnd.services.customer_insights import generate_customer_insights_from_sales


class TestCustomerHistory(unittest.TestCase):
    def test_full_history_overrides_first_order_for_new_customer_logic(self):
        current_df = pd.DataFrame(
            {
                "Order Number": ["1002"],
                "Order Date": ["2026-04-05 10:00:00"],
                "Customer Name": ["Jane Doe"],
                "Email": ["jane@example.com"],
                "Qty": [1],
                "Item Name": ["Polo"],
                "Order Total Amount": [1000],
            }
        )
        history_df = pd.DataFrame(
            {
                "Order Number": ["0999", "1002"],
                "Order Date": ["2026-03-01 09:00:00", "2026-04-05 10:00:00"],
                "Customer Name": ["Jane Doe", "Jane Doe"],
                "Email": ["jane@example.com", "jane@example.com"],
                "Qty": [1, 1],
                "Item Name": ["Cap", "Polo"],
                "Order Total Amount": [500, 1000],
            }
        )

        customers = generate_customer_insights_from_sales(current_df, full_history_df=history_df)

        self.assertEqual(len(customers), 1)
        self.assertEqual(str(customers.loc[0, "first_order"]), "2026-03-01 09:00:00")
        self.assertEqual(int(customers.loc[0, "total_orders"]), 2)
        self.assertEqual(float(customers.loc[0, "total_revenue"]), 1500.0)
        self.assertEqual(int(customers.loc[0, "current_orders"]), 1)
        self.assertEqual(float(customers.loc[0, "current_revenue"]), 1000.0)


if __name__ == "__main__":
    unittest.main()
