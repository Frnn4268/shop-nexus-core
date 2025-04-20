package repository

import (
	"context"

	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/bson/primitive"
	"go.mongodb.org/mongo-driver/mongo"
)

type ProductRepository struct {
	collection *mongo.Collection
}

func NewProductRepository(db *mongo.Database) *ProductRepository {
	return &ProductRepository{
		collection: db.Collection("products"),
	}
}

func (r *ProductRepository) ProductExists(ctx context.Context, productID string) (bool, error) {
	objID, err := primitive.ObjectIDFromHex(productID)
	if err != nil {
		return false, nil
	}

	count, err := r.collection.CountDocuments(ctx, bson.M{"_id": objID})
	if err != nil {
		return false, err
	}

	return count > 0, nil
}
