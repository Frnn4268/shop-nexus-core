package models

import (
	"time"

	"go.mongodb.org/mongo-driver/bson/primitive"
)

type OrderStatus string

const (
	StatusPending   OrderStatus = "pending"
	StatusCompleted OrderStatus = "completed"
	StatusCancelled OrderStatus = "cancelled"
)

type OrderItem struct {
	ProductID string  `bson:"product_id" json:"product_id"`
	Quantity  int     `bson:"quantity"`
	Price     float64 `bson:"price"`
}

type Order struct {
	ID        primitive.ObjectID `bson:"_id,omitempty" json:"id,omitempty"`
	UserID    primitive.ObjectID `bson:"user_id" json:"user_id"`
	Items     []OrderItem        `bson:"items" json:"items"`
	Total     float64            `bson:"total" json:"total"`
	Status    OrderStatus        `bson:"status" json:"status"`
	CreatedAt time.Time          `bson:"created_at" json:"created_at"`
	UpdatedAt time.Time          `bson:"updated_at" json:"updated_at"`
}
