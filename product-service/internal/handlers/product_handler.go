package handlers

import (
	"net/http"
	"product-service/internal/models"
	"product-service/internal/repository"
	"product-service/internal/utils"
	"time"

	"github.com/gin-gonic/gin"
	"go.mongodb.org/mongo-driver/bson/primitive"
)

type ProductHandler struct {
	repo *repository.ProductRepository
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
	return &ProductHandler{repo: repo}
}

// POST /products
func (h *ProductHandler) CreateProduct(c *gin.Context) {
	var req CreateProductRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Convertir y validar Category IDs
	var categoryIDs []primitive.ObjectID
	for _, catIDStr := range req.CategoryIDs {
		catID, err := primitive.ObjectIDFromHex(catIDStr)
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid category ID format"})
			return
		}

		// Verificar existencia de la categoría
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

	// Crear producto real
	product := models.Product{
		Name:        req.Name,
		Description: req.Description,
		Price:       req.Price,
		CategoryIDs: categoryIDs,
		CreatedAt:   time.Now(), // Ya no lo asignamos en el repositorio
	}

	if err := h.repo.CreateProduct(c.Request.Context(), &product); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Error creating product"})
		return
	}

	// Crear respuesta con el ID correcto
	response := ProductResponse{
		ID:          product.ID.Hex(), // Convertir a string
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

	// Convertir y validar categorías
	var categoryIDs []primitive.ObjectID
	for _, catIDStr := range req.CategoryIDs {
		catID, err := primitive.ObjectIDFromHex(catIDStr)
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid category ID format"})
			return
		}

		// Validar existencia de categoría
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

	// Obtener producto actualizado para la respuesta
	updatedProduct, err := h.repo.GetProductByID(c.Request.Context(), id)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Error retrieving updated product"})
		return
	}

	// Convertir a response
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

	// Verificar si el producto existe primero
	_, err := h.repo.GetProductByID(c.Request.Context(), id)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Product not found"})
		return
	}

	// Proceder con la eliminación
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

	// Forzar la generación de nuevo ID
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
