package events

import (
	"encoding/json"
	"fmt"
	"log"
	"time"

	"github.com/streadway/amqp"
)

type EventPublisher struct {
	conn *amqp.Connection
}

const (
	orderCreatedExchange = "order_created"
	orderCreatedQueue    = "order_created"
	orderCreatedKey      = "order_created"
)

// NewEventPublisher creates a new publisher instance.
func NewEventPublisher(uri string) (*EventPublisher, error) {
	if uri == "" {
		return nil, fmt.Errorf("rabbitmq uri is empty")
	}

	maxRetries := 10
	var conn *amqp.Connection
	var err error

	for i := 0; i < maxRetries; i++ {
		conn, err = amqp.Dial(uri)
		if err == nil {
			return &EventPublisher{conn: conn}, nil
		}
		log.Printf("RabbitMQ connection attempt %d/%d failed. Retrying in 5 seconds.", i+1, maxRetries)
		time.Sleep(5 * time.Second)
	}

	return nil, fmt.Errorf("failed to connect after %d attempts: %w", maxRetries, err)
}

func (p *EventPublisher) ensureTopology(ch *amqp.Channel) error {
	if err := ch.ExchangeDeclare(orderCreatedExchange, "direct", true, false, false, false, nil); err != nil {
		return err
	}

	if _, err := ch.QueueDeclare(orderCreatedQueue, true, false, false, false, amqp.Table{
		"x-message-ttl": int32(86400000),
		"x-queue-type":  "classic",
	}); err != nil {
		return err
	}

	return ch.QueueBind(orderCreatedQueue, orderCreatedKey, orderCreatedExchange, false, nil)
}

func (p *EventPublisher) PublishOrderCreated(order interface{}) error {
	if p == nil || p.conn == nil {
		return fmt.Errorf("rabbitmq publisher is not initialized")
	}

	ch, err := p.conn.Channel()
	if err != nil {
		return err
	}
	defer ch.Close()

	if err := p.ensureTopology(ch); err != nil {
		return err
	}

	body, err := json.Marshal(order)
	if err != nil {
		return err
	}

	return ch.Publish(
		orderCreatedExchange,
		orderCreatedKey,
		false, // mandatory
		false, // immediate
		amqp.Publishing{
			DeliveryMode: amqp.Persistent,
			ContentType:  "application/json",
			Body:         body,
		},
	)
}

func (p *EventPublisher) Close() {
	if p.conn != nil {
		p.conn.Close()
	}
}
