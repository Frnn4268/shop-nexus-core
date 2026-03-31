package events

import (
	"order-service/internal/models"
	"time"
)

const OrderCreatedEventType = "order.created"

type OrderCreatedData struct {
	OrderID    string  `json:"order_id"`
	UserID     string  `json:"user_id"`
	Total      float64 `json:"total"`
	Status     string  `json:"status"`
	ItemsCount int     `json:"items_count"`
}

type OrderCreatedEvent struct {
	EventID       string           `json:"event_id"`
	EventType     string           `json:"event_type"`
	OccurredAt    string           `json:"occurred_at"`
	CorrelationID string           `json:"correlation_id,omitempty"`
	Data          OrderCreatedData `json:"data"`
}

func NewOrderCreatedEvent(order models.Order, correlationID string) OrderCreatedEvent {
	return OrderCreatedEvent{
		EventID:       order.ID.Hex(),
		EventType:     OrderCreatedEventType,
		OccurredAt:    time.Now().UTC().Format(time.RFC3339Nano),
		CorrelationID: correlationID,
		Data: OrderCreatedData{
			OrderID:    order.ID.Hex(),
			UserID:     order.UserID.Hex(),
			Total:      order.Total,
			Status:     string(order.Status),
			ItemsCount: len(order.Items),
		},
	}
}
