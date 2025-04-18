package payment

import (
	"log"
	"math/rand"
	"time"

	"go.mongodb.org/mongo-driver/bson/primitive"
)

type PaymentResponse struct {
	Success   bool
	PaymentID string
}

// Simula una pasarela de pago (ej: Stripe)
func ProcessPayment(amount float64) PaymentResponse {
	rand.Seed(time.Now().UnixNano())
	success := rand.Float32() < 0.8

	if !success {
		log.Println("⚠️ Pago fallido (simulado)")
	}

	return PaymentResponse{
		Success:   success,
		PaymentID: "pay_" + primitive.NewObjectID().Hex(),
	}
}
