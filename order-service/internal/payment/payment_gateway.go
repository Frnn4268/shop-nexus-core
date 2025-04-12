package payment

import (
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

	// Simular éxito en el 80% de los casos
	success := rand.Float32() < 0.8

	return PaymentResponse{
		Success:   success,
		PaymentID: "pay_" + primitive.NewObjectID().Hex(),
	}
}
