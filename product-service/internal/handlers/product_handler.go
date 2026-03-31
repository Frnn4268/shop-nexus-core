package handlers

import (
	"context"
	"net/http"
	"product-service/internal/models"
	"product-service/internal/repository"
	"product-service/internal/utils"
	"time"

	"github.com/gin-gonic/gin"
	"go.mongodb.org/mongo-driver/bson/primitive"
)

type productStore interface {
	CreateProduct(ctx context.Context, product *models.Product) error
	GetAllProducts(ctx context.Context, categoryID string) ([]models.Product, error)
	GetProductByID(ctx context.Context, id string) (*models.Product, error)
	UpdateProduct(ctx context.Context, id primitive.ObjectID, product *models.Product) error
	DeleteProduct(ctx context.Context, id primitive.ObjectID) error
	CategoryExists(ctx context.Context, id primitive.ObjectID) (bool, error)
	CreateCategory(ctx context.Context, category *models.Category) error
	GetAllCategories(ctx context.Context) ([]models.Category, error)
}

type ProductHandler struct {
	repo productStore
}

type CreateProductRequest struct {
	Name        string   `json:"name"`
	Description string   `json:"description"`
	Price       float64  `json:"price"`
	CategoryIDs []string `json:"category_ids"`
}

type UpdateProductRequest struct {
	Name        string   `json:"name"`
	Description string   `json:"description"`
	Price       float64  `json:"price"`
	CategoryIDs []string `json:"category_ids"`
}

type ProductResponse struct {
	ID          string    `json:"id"`
	Name        string    `json:"name"`
	Description string    `json:"description"`
	Price       float64   `json:"price"`
	CategoryIDs []string  `json:"category_ids"`
	CreatedAt   time.Time `json:"created_at"`
}

type CategoryResponse struct {
	ID   string `json:"id"`
	Name string `json:"name"`
}

func NewProductHandler(repo *repository.ProductRepository) *ProductHandler {
	return NewProductHandlerWithDependencies(repo)
}

func NewProductHandlerWithDependencies(repo productStore) *ProductHandler {
	return &ProductHandler{repo: repo}
}

// POST /products
func (h *ProductHandler) CreateProduct(c *gin.Context) {
	var req CreateProductRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Convert and validate category IDs.
	var categoryIDs []primitive.ObjectID
	for _, catIDStr := range req.CategoryIDs {
		catID, err := primitive.ObjectIDFromHex(catIDStr)
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid category ID format"})
			return
		}

		// Verify that the referenced category exists.
		exists, err := h.repo.CategoryExists(c.Request.Context(), catID)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Error verifying category"})
			return
		}
		if !exists {
			c.JSON(http.StatusBadRequest, gin.H{"error": "Category does not exist: " + catIDStr})
			return
		}

		categoryIDs = append(categoryIDs, catID)
	}

	// Build the product model that will be persisted.
	product := models.Product{
		Name:        req.Name,
		Description: req.Description,
		Price:       req.Price,
		CategoryIDs: categoryIDs,
		CreatedAt:   time.Now(),
	}

	if err := h.repo.CreateProduct(c.Request.Context(), &product); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Error creating product"})
		return
	}

	// Build the response using the generated identifier.
	response := ProductResponse{
		ID:          product.ID.Hex(),
		Name:        product.Name,
		Description: product.Description,
		Price:       product.Price,
		CategoryIDs: req.CategoryIDs,
		CreatedAt:   product.CreatedAt,
	}

	c.JSON(http.StatusCreated, response)
}

// GET /products
func (h *ProductHandler) GetAllProducts(c *gin.Context) {
	categoryID := c.Query("category")
	products, err := h.repo.GetAllProducts(c.Request.Context(), categoryID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Error retrieving products"})
		return
	}
	c.JSON(http.StatusOK, products)
}

// GET /products/:id
func (h *ProductHandler) GetProductByID(c *gin.Context) {
	product, err := h.repo.GetProductByID(c.Request.Context(), c.Param("id"))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Product not found"})
		return
	}
	c.JSON(http.StatusOK, product)
}

func (h *ProductHandler) UpdateProduct(c *gin.Context) {
	id := c.Param("id")
	objID, valid := utils.ValidateObjectID(c, id)
	if !valid {
		return
	}

	var req UpdateProductRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Convert and validate categories.
	var categoryIDs []primitive.ObjectID
	for _, catIDStr := range req.CategoryIDs {
		catID, err := primitive.ObjectIDFromHex(catIDStr)
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid category ID format"})
			return
		}

		// Validate category existence before updating the product.
		exists, err := h.repo.CategoryExists(c.Request.Context(), catID)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Error verifying category"})
			return
		}
		if !exists {
			c.JSON(http.StatusBadRequest, gin.H{"error": "Category does not exist: " + catIDStr})
			return
		}
		categoryIDs = append(categoryIDs, catID)
	}

	updateData := models.Product{
		Name:        req.Name,
		Description: req.Description,
		Price:       req.Price,
		CategoryIDs: categoryIDs,
	}

	if err := h.repo.UpdateProduct(c.Request.Context(), objID, &updateData); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Error updating product"})
		return
	}

	// Read the updated product back for the response payload.
	updatedProduct, err := h.repo.GetProductByID(c.Request.Context(), id)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Error retrieving updated product"})
		return
	}

	// Map the updated entity into the API response.
	response := ProductResponse{
		ID:          updatedProduct.ID.Hex(),
		Name:        updatedProduct.Name,
		Description: updatedProduct.Description,
		Price:       updatedProduct.Price,
		CategoryIDs: req.CategoryIDs,
		CreatedAt:   updatedProduct.CreatedAt,
	}

	c.JSON(http.StatusOK, response)
}

func (h *ProductHandler) DeleteProduct(c *gin.Context) {
	id := c.Param("id")
	objID, valid := utils.ValidateObjectID(c, id)
	if !valid {
		return
	}

	// Check whether the product exists before deleting it.
	_, err := h.repo.GetProductByID(c.Request.Context(), id)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Product not found"})
		return
	}

	// Proceed with deletion once existence is confirmed.
	if err := h.repo.DeleteProduct(c.Request.Context(), objID); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Error deleting product"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "Product deleted successfully"})
}

// POST /categories
func (h *ProductHandler) CreateCategory(c *gin.Context) {
	var category models.Category
	if err := c.ShouldBindJSON(&category); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Force a new identifier to be generated by MongoDB.
	category.ID = primitive.NilObjectID

	if err := h.repo.CreateCategory(c.Request.Context(), &category); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Error creating category"})
		return
	}

	c.JSON(http.StatusCreated, category)
}

// GET /categories
func (h *ProductHandler) GetAllCategories(c *gin.Context) {
	categories, err := h.repo.GetAllCategories(c.Request.Context())
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Error retrieving categories"})
		return
	}
	c.JSON(http.StatusOK, categories)
}
