package repository

import (
	"context"
	"order-service/internal/models"
	"time"

	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/bson/primitive"
	"go.mongodb.org/mongo-driver/mongo"
)

type OrderRepository struct {
	collection *mongo.Collection
}

func NewOrderRepository(db *mongo.Database) *OrderRepository {
	return &OrderRepository{
		collection: db.Collection("orders"),
	}
}

func (r *OrderRepository) CreateOrder(ctx context.Context, order *models.Order) error {
	order.CreatedAt = time.Now()
	order.UpdatedAt = time.Now()

	result, err := r.collection.InsertOne(ctx, order)
	if err != nil {
		return err
	}

	if oid, ok := result.InsertedID.(primitive.ObjectID); ok {
		order.ID = oid
	}

	return nil
}

func (r *OrderRepository) GetOrderByID(ctx context.Context, id string) (*models.Order, error) {
	objID, _ := primitive.ObjectIDFromHex(id)
	var order models.Order
	err := r.collection.FindOne(ctx, bson.M{"_id": objID}).Decode(&order)
	return &order, err
}

func (r *OrderRepository) GetAllOrders(ctx context.Context) ([]models.Order, error) {
	cursor, err := r.collection.Find(ctx, bson.M{})
	if err != nil {
		return nil, err
	}

	var orders []models.Order
	if err = cursor.All(ctx, &orders); err != nil {
		return nil, err
	}
	return orders, nil
}
