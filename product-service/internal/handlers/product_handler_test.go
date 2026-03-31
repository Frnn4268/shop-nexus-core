package handlers

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"net/http"
	"net/http/httptest"
	"product-service/internal/models"
	"testing"
	"time"

	"github.com/gin-gonic/gin"
	"go.mongodb.org/mongo-driver/bson/primitive"
)

type fakeProductStore struct {
	products          map[string]*models.Product
	categories        map[string]*models.Category
	createdProducts   []*models.Product
	createdCategory   *models.Category
	createProductErr  error
	updateProductErr  error
	deleteProductErr  error
	getProductErr     error
	categoryExistsErr error
}

func newFakeProductStore() *fakeProductStore {
	return &fakeProductStore{
		products:   make(map[string]*models.Product),
		categories: make(map[string]*models.Category),
	}
}

func (f *fakeProductStore) CreateProduct(_ context.Context, product *models.Product) error {
	if f.createProductErr != nil {
		return f.createProductErr
	}
	clone := *product
	if clone.ID.IsZero() {
		clone.ID = primitive.NewObjectID()
	}
	if clone.CreatedAt.IsZero() {
		clone.CreatedAt = time.Now()
	}
	*product = clone
	f.products[clone.ID.Hex()] = &clone
	f.createdProducts = append(f.createdProducts, &clone)
	return nil
}

func (f *fakeProductStore) GetAllProducts(_ context.Context, _ string) ([]models.Product, error) {
	products := make([]models.Product, 0, len(f.products))
	for _, product := range f.products {
		products = append(products, *product)
	}
	return products, nil
}

func (f *fakeProductStore) GetProductByID(_ context.Context, id string) (*models.Product, error) {
	if f.getProductErr != nil {
		return nil, f.getProductErr
	}
	product, ok := f.products[id]
	if !ok {
		return nil, errors.New("product not found")
	}
	clone := *product
	return &clone, nil
}

func (f *fakeProductStore) UpdateProduct(_ context.Context, id primitive.ObjectID, product *models.Product) error {
	if f.updateProductErr != nil {
		return f.updateProductErr
	}
	existing, ok := f.products[id.Hex()]
	if !ok {
		return errors.New("product not found")
	}
	existing.Name = product.Name
	existing.Description = product.Description
	existing.Price = product.Price
	existing.CategoryIDs = product.CategoryIDs
	return nil
}

func (f *fakeProductStore) DeleteProduct(_ context.Context, id primitive.ObjectID) error {
	if f.deleteProductErr != nil {
		return f.deleteProductErr
	}
	if _, ok := f.products[id.Hex()]; !ok {
		return errors.New("product not found")
	}
	delete(f.products, id.Hex())
	return nil
}

func (f *fakeProductStore) CategoryExists(_ context.Context, id primitive.ObjectID) (bool, error) {
	if f.categoryExistsErr != nil {
		return false, f.categoryExistsErr
	}
	_, ok := f.categories[id.Hex()]
	return ok, nil
}

func (f *fakeProductStore) CreateCategory(_ context.Context, category *models.Category) error {
	clone := *category
	if clone.ID.IsZero() {
		clone.ID = primitive.NewObjectID()
	}
	*category = clone
	f.categories[clone.ID.Hex()] = &clone
	f.createdCategory = &clone
	return nil
}

func (f *fakeProductStore) GetAllCategories(_ context.Context) ([]models.Category, error) {
	categories := make([]models.Category, 0, len(f.categories))
	for _, category := range f.categories {
		categories = append(categories, *category)
	}
	return categories, nil
}

func TestCreateProductPersistsValidatedCategoryIDs(t *testing.T) {
	gin.SetMode(gin.TestMode)
	repo := newFakeProductStore()
	categoryID := primitive.NewObjectID()
	repo.categories[categoryID.Hex()] = &models.Category{ID: categoryID, Name: "Office"}
	handler := NewProductHandlerWithDependencies(repo)

	recorder := httptest.NewRecorder()
	ctx, _ := gin.CreateTestContext(recorder)
	ctx.Request = newProductJSONRequest(t, http.MethodPost, "/products", map[string]any{
		"name":         "Desk",
		"description":  "Standing desk",
		"price":        199.99,
		"category_ids": []string{categoryID.Hex()},
	})

	handler.CreateProduct(ctx)

	if recorder.Code != http.StatusCreated {
		t.Fatalf("expected status %d, got %d with body %s", http.StatusCreated, recorder.Code, recorder.Body.String())
	}
	if len(repo.createdProducts) != 1 {
		t.Fatalf("expected one created product, got %d", len(repo.createdProducts))
	}
	created := repo.createdProducts[0]
	if len(created.CategoryIDs) != 1 || created.CategoryIDs[0] != categoryID {
		t.Fatalf("expected category id %s to be persisted, got %#v", categoryID.Hex(), created.CategoryIDs)
	}
}

func TestCreateProductRejectsUnknownCategory(t *testing.T) {
	gin.SetMode(gin.TestMode)
	handler := NewProductHandlerWithDependencies(newFakeProductStore())
	missingCategoryID := primitive.NewObjectID().Hex()

	recorder := httptest.NewRecorder()
	ctx, _ := gin.CreateTestContext(recorder)
	ctx.Request = newProductJSONRequest(t, http.MethodPost, "/products", map[string]any{
		"name":         "Desk",
		"description":  "Standing desk",
		"price":        199.99,
		"category_ids": []string{missingCategoryID},
	})

	handler.CreateProduct(ctx)

	if recorder.Code != http.StatusBadRequest {
		t.Fatalf("expected status %d, got %d with body %s", http.StatusBadRequest, recorder.Code, recorder.Body.String())
	}
}

func TestUpdateProductReturnsUpdatedPayload(t *testing.T) {
	gin.SetMode(gin.TestMode)
	repo := newFakeProductStore()
	categoryID := primitive.NewObjectID()
	repo.categories[categoryID.Hex()] = &models.Category{ID: categoryID, Name: "Office"}
	productID := primitive.NewObjectID()
	repo.products[productID.Hex()] = &models.Product{
		ID:          productID,
		Name:        "Old Desk",
		Description: "Old",
		Price:       99.99,
		CategoryIDs: []primitive.ObjectID{categoryID},
		CreatedAt:   time.Now(),
	}
	handler := NewProductHandlerWithDependencies(repo)

	recorder := httptest.NewRecorder()
	ctx, _ := gin.CreateTestContext(recorder)
	ctx.Params = gin.Params{{Key: "id", Value: productID.Hex()}}
	ctx.Request = newProductJSONRequest(t, http.MethodPut, "/products/"+productID.Hex(), map[string]any{
		"name":         "New Desk",
		"description":  "Updated",
		"price":        149.99,
		"category_ids": []string{categoryID.Hex()},
	})

	handler.UpdateProduct(ctx)

	if recorder.Code != http.StatusOK {
		t.Fatalf("expected status %d, got %d with body %s", http.StatusOK, recorder.Code, recorder.Body.String())
	}
	if repo.products[productID.Hex()].Name != "New Desk" {
		t.Fatalf("expected product name to be updated, got %q", repo.products[productID.Hex()].Name)
	}
}

func TestDeleteProductReturnsNotFoundWhenProductDoesNotExist(t *testing.T) {
	gin.SetMode(gin.TestMode)
	handler := NewProductHandlerWithDependencies(newFakeProductStore())
	productID := primitive.NewObjectID()

	recorder := httptest.NewRecorder()
	ctx, _ := gin.CreateTestContext(recorder)
	ctx.Params = gin.Params{{Key: "id", Value: productID.Hex()}}
	ctx.Request = httptest.NewRequest(http.MethodDelete, "/products/"+productID.Hex(), nil)

	handler.DeleteProduct(ctx)

	if recorder.Code != http.StatusNotFound {
		t.Fatalf("expected status %d, got %d with body %s", http.StatusNotFound, recorder.Code, recorder.Body.String())
	}
}

func newProductJSONRequest(t *testing.T, method string, target string, payload any) *http.Request {
	t.Helper()
	body, err := json.Marshal(payload)
	if err != nil {
		t.Fatalf("failed to marshal payload: %v", err)
	}

	request := httptest.NewRequest(method, target, bytes.NewReader(body))
	request.Header.Set("Content-Type", "application/json")
	return request
}
