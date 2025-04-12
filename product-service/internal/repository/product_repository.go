package repository

import (
	"context"
	"product-service/internal/models"
	"time"

	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/bson/primitive"
	"go.mongodb.org/mongo-driver/mongo"
)

type ProductRepository struct {
	productsColl   *mongo.Collection
	categoriesColl *mongo.Collection
}

func NewProductRepository(db *mongo.Database) *ProductRepository {
	return &ProductRepository{
		productsColl:   db.Collection("products"),
		categoriesColl: db.Collection("categories"),
	}
}

// Operaciones CRUD para Productos
func (r *ProductRepository) CreateProduct(ctx context.Context, product *models.Product) error {
	product.CreatedAt = time.Now()
	_, err := r.productsColl.InsertOne(ctx, product)
	return err
}

func (r *ProductRepository) GetAllProducts(ctx context.Context, categoryID string) ([]models.Product, error) {
	filter := bson.M{}
	if categoryID != "" {
		objID, _ := primitive.ObjectIDFromHex(categoryID)
		filter["category_ids"] = objID
	}

	cursor, err := r.productsColl.Find(ctx, filter)
	if err != nil {
		return nil, err
	}

	var products []models.Product
	if err = cursor.All(ctx, &products); err != nil {
		return nil, err
	}
	return products, nil
}

func (r *ProductRepository) GetProductByID(ctx context.Context, id string) (*models.Product, error) {
	objID, _ := primitive.ObjectIDFromHex(id)
	var product models.Product
	err := r.productsColl.FindOne(ctx, bson.M{"_id": objID}).Decode(&product)
	return &product, err
}

// Operaciones CRUD para Categorías
func (r *ProductRepository) CreateCategory(ctx context.Context, category *models.Category) error {
	_, err := r.categoriesColl.InsertOne(ctx, category)
	return err
}

func (r *ProductRepository) GetAllCategories(ctx context.Context) ([]models.Category, error) {
	cursor, err := r.categoriesColl.Find(ctx, bson.M{})
	if err != nil {
		return nil, err
	}

	var categories []models.Category
	if err = cursor.All(ctx, &categories); err != nil {
		return nil, err
	}
	return categories, nil
}
