package payment

import (
	"log"
	"math/rand"
	"time"

	"go.mongodb.org/mongo-driver/bson/primitive"
)

type Processor struct {
	successRate float64
}

// NewProcessor crea una nueva instancia del procesador de pagos
func NewProcessor(successRate float64) *Processor {
	rand.Seed(time.Now().UnixNano())
	return &Processor{successRate: successRate}
}

type Response struct {
	Success   bool   `json:"success"`
	PaymentID string `json:"payment_id"`
}

func (p *Processor) Process(amount float64) Response {
	success := rand.Float32() < float32(p.successRate)
	paymentID := "pay_" + primitive.NewObjectID().Hex()

	if !success {
		log.Println("⚠️ Pago fallido (simulado)")
	}

	return Response{
		Success:   success,
		PaymentID: paymentID,
	}
}
