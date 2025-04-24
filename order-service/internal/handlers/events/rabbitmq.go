package events

import (
    "encoding/json"
    "log"
    "time"

    "github.com/streadway/amqp"
)

type EventPublisher struct {
    conn *amqp.Connection
}

// NewEventPublisher crea una nueva instancia del publicador
func NewEventPublisher(uri string) (*EventPublisher, error) {
    maxRetries := 3
    var conn *amqp.Connection
    var err error

    for i := 0; i < maxRetries; i++ {
        conn, err = amqp.Dial(uri)
        if err == nil {
            break
        }
        log.Printf("Intento %d/%d: Error conectando a RabbitMQ: %v", i+1, maxRetries, err)
        time.Sleep(2 * time.Second)
    }

    if err != nil {
        return nil, err
    }

    return &EventPublisher{conn: conn}, nil
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