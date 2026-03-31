import unittest
from unittest.mock import Mock, patch

from flask import Flask

from app.api.routes import create_blueprint
from app.services.health_service import HealthService
from app.services.order_notification_service import OrderEvent, OrderNotificationService


class NotificationHealthServiceTests(unittest.TestCase):
    def test_health_is_healthy_only_when_rabbitmq_and_celery_are_ready(self):
        service = HealthService(Mock())

        with patch.object(service, "_check_rabbitmq_connection", return_value={"status": "connected", "error": None}), patch.object(
            service,
            "_check_celery_status",
            return_value={"status": "active", "error": None},
        ):
            payload = service.get_health()

        self.assertEqual(payload["status"], "healthy")

    def test_health_is_degraded_when_celery_is_inactive(self):
        service = HealthService(Mock())

        with patch.object(service, "_check_rabbitmq_connection", return_value={"status": "connected", "error": None}), patch.object(
            service,
            "_check_celery_status",
            return_value={"status": "inactive", "error": None},
        ):
            payload = service.get_health()

        self.assertEqual(payload["status"], "degraded")


class NotificationRouteTests(unittest.TestCase):
    def test_health_route_returns_503_for_degraded_state(self):
        app = Flask(__name__)
        health_service = Mock()
        health_service.get_health.return_value = {"status": "degraded", "services": {}}
        app.register_blueprint(create_blueprint(health_service))

        response = app.test_client().get("/health")

        self.assertEqual(response.status_code, 503)


class OrderNotificationServiceTests(unittest.TestCase):
    def test_parse_order_event_requires_expected_fields(self):
        with self.assertRaisesRegex(ValueError, "missing required fields"):
            OrderNotificationService.parse_order_event({"ID": "1"})

    def test_parse_order_event_accepts_explicit_event_envelope(self):
        event = OrderNotificationService.parse_order_event(
            {
                "event_type": "order.created",
                "correlation_id": "req-123",
                "data": {
                    "order_id": "order-1",
                    "user_id": "user-99",
                    "total": 42.5,
                },
            }
        )

        self.assertEqual(event.order_id, "order-1")
        self.assertEqual(event.user_id, "user-99")
        self.assertEqual(event.correlation_id, "req-123")

    def test_schedule_notifications_enqueues_email_and_sms(self):
        service = OrderNotificationService()
        order_event = OrderEvent(order_id="order-1", user_id="user-99", total=42.5)

        with patch("app.services.order_notification_service.send_email.delay") as email_delay, patch(
            "app.services.order_notification_service.send_sms.delay"
        ) as sms_delay:
            service.schedule_notifications(order_event)

        email_delay.assert_called_once()
        sms_delay.assert_called_once()
        self.assertIn("user-99", email_delay.call_args.args[0])
        self.assertIn("42.5", sms_delay.call_args.args[1])


if __name__ == "__main__":
    unittest.main()