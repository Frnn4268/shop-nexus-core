import unittest

from app.workers.order_retraining_consumer import OrderRetrainingConsumer


class OrderRetrainingConsumerTests(unittest.TestCase):
    def test_supported_event_accepts_explicit_envelope(self):
        self.assertTrue(
            OrderRetrainingConsumer._is_supported_order_event(
                {
                    "event_type": "order.created",
                    "data": {
                        "order_id": "order-1",
                        "user_id": "user-1",
                        "total": 10.0,
                    },
                }
            )
        )

    def test_supported_event_accepts_legacy_payload(self):
        self.assertTrue(
            OrderRetrainingConsumer._is_supported_order_event(
                {"ID": "order-1", "UserID": "user-1", "Total": 10.0}
            )
        )

    def test_supported_event_rejects_unrelated_payload(self):
        self.assertFalse(OrderRetrainingConsumer._is_supported_order_event({"event_type": "other"}))


if __name__ == "__main__":
    unittest.main()