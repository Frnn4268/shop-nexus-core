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

	result, err := r.productsColl.InsertOne(ctx, product)
	if err != nil {
		return err
	}

	// Asignar el ID generado
	if oid, ok := result.InsertedID.(primitive.ObjectID); ok {
		product.ID = oid
	}
	return nil
}

func (r *ProductRepository) GetAllProducts(ctx context.Context, categoryID string) ([]models.Product, error) {
	filter := bson.M{}
	if categoryID != "" {
		objID, err := primitive.ObjectIDFromHex(categoryID)
		if err != nil {
			return nil, err
		}
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

// Métodos adicionales para Update y Delete
func (r *ProductRepository) UpdateProduct(ctx context.Context, id primitive.ObjectID, product *models.Product) error {
	update := bson.M{
		"$set": bson.M{
			"name":         product.Name,
			"description":  product.Description,
			"price":        product.Price,
			"category_ids": product.CategoryIDs,
		},
	}

	_, err := r.productsColl.UpdateByID(ctx, id, update)
	return err
}

func (r *ProductRepository) DeleteProduct(ctx context.Context, id primitive.ObjectID) error {
	result, err := r.productsColl.DeleteOne(ctx, bson.M{"_id": id})
	if err != nil {
		return err
	}

	if result.DeletedCount == 0 {
		return err
	}

	return nil
}

// Operaciones CRUD para Categorías
func (r *ProductRepository) CategoryExists(ctx context.Context, id primitive.ObjectID) (bool, error) {
	count, err := r.categoriesColl.CountDocuments(ctx, bson.M{"_id": id})
	return count > 0, err
}

func (r *ProductRepository) CreateCategory(ctx context.Context, category *models.Category) error {
	result, err := r.categoriesColl.InsertOne(ctx, category)
	if err != nil {
		return err
	}

	// Asignar el ID generado
	if oid, ok := result.InsertedID.(primitive.ObjectID); ok {
		category.ID = oid
	}
	return nil
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
