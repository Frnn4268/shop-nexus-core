package models

import (
	"time"

	"go.mongodb.org/mongo-driver/bson/primitive"
)

type Product struct {
	ID          primitive.ObjectID   `bson:"_id,omitempty"`
	Name        string               `bson:"name"`
	Description string               `bson:"description"`
	Price       float64              `bson:"price"`
	CategoryIDs []primitive.ObjectID `bson:"category_ids"`
	CreatedAt   time.Time            `bson:"created_at"`
}

type Category struct {
	ID   primitive.ObjectID `bson:"_id,omitempty"`
	Name string             `bson:"name"`
}
