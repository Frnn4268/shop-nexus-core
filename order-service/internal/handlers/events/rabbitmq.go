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

// NewEventPublisher crea una nueva instancia del publicador
func NewEventPublisher(uri string) (*EventPublisher, error) {
    maxRetries := 10  // Aumentar reintentos
    var conn *amqp.Connection
    var err error

    for i := 0; i < maxRetries; i++ {
        conn, err = amqp.Dial(uri)
        if err == nil {
            return &EventPublisher{conn: conn}, nil
        }
        log.Printf("Intento %d/%d fallido. Esperando 5 segundos...", i+1, maxRetries)
        time.Sleep(5 * time.Second)
    }

    return nil, fmt.Errorf("no se pudo conectar después de %d intentos: %v", maxRetries, err)
}

func (p *EventPublisher) PublishOrderCreated(order interface{}) error {
    ch, err := p.conn.Channel()
    if err != nil {
        return err
    }
    defer ch.Close()

    _, err = ch.QueueDeclare(
        "order_created",
        true,  // Durable
        false, // AutoDelete
        false, // Exclusive
        false, // NoWait
        nil,
    )
    if err != nil {
        return err
    }

    body, err := json.Marshal(order)
    if err != nil {
        return err
    }

    return ch.Publish(
        "",
        "order_created",
        false,
        false,
        amqp.Publishing{
            DeliveryMode: amqp.Persistent,
            ContentType:  "application/json",
            Body:        body,
        },
    )
}

func (p *EventPublisher) Close() {
    if p.conn != nil {
        p.conn.Close()
    }
}