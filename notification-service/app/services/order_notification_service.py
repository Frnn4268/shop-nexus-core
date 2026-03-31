from dataclasses import dataclass

from app.core.config import settings
from app.tasks.notifications import send_email, send_sms


@dataclass(frozen=True)
class OrderEvent:
    order_id: str
    user_id: str
    total: float
    correlation_id: str | None = None


class OrderNotificationService:
    @staticmethod
    def parse_order_event(payload: dict) -> OrderEvent:
        event_payload = OrderNotificationService._extract_event_payload(payload)
        required_fields = ["order_id", "total", "user_id"]
        legacy_required_fields = ["ID", "Total", "UserID"]

        if all(field in event_payload for field in required_fields):
            return OrderEvent(
                order_id=str(event_payload["order_id"]),
                user_id=str(event_payload["user_id"]),
                total=float(event_payload["total"]),
                correlation_id=str(payload.get("correlation_id") or "").strip() or None,
            )

        missing_fields = [field for field in legacy_required_fields if field not in event_payload]
        if missing_fields:
            raise ValueError(f"Event payload is missing required fields: {', '.join(missing_fields)}")

        return OrderEvent(
            order_id=str(event_payload["ID"]),
            user_id=str(event_payload["UserID"]),
            total=float(event_payload["Total"]),
            correlation_id=str(payload.get("correlation_id") or "").strip() or None,
        )

    @staticmethod
    def _extract_event_payload(payload: dict) -> dict:
        if isinstance(payload.get("data"), dict):
            return payload["data"]
        return payload

    def schedule_notifications(self, order_event: OrderEvent) -> None:
        email = f"user{order_event.user_id}@{settings.notification_email_domain}"
        phone = settings.notification_phone_default

        send_email.delay(
            email,
            f"Order {order_event.order_id} confirmed",
            f"Order total: ${order_event.total}",
        )
        send_sms.delay(
            phone,
            f"Thank you for your order totaling ${order_event.total}",
        )