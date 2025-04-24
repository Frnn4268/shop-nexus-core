package handlers

import (
	"net/http"
	"product-service/internal/models"
	"product-service/internal/repository"

	"github.com/gin-gonic/gin"
	"go.mongodb.org/mongo-driver/bson/primitive"
)

type CategoryHandler struct {
	repo *repository.ProductRepository
}

func NewCategoryHandler(repo *repository.ProductRepository) *CategoryHandler {
	return &CategoryHandler{repo: repo}
}

// POST /categories
func (h *CategoryHandler) CreateCategory(c *gin.Context) {
	var category models.Category
	if err := c.ShouldBindJSON(&category); err != nil {
		ErrorResponse(c, http.StatusBadRequest, err.Error())
		return
	}

	category.ID = primitive.NilObjectID // Reset ID

	if err := h.repo.CreateCategory(c.Request.Context(), &category); err != nil {
		ErrorResponse(c, http.StatusInternalServerError, "Error creating category")
		return
	}

	SuccessResponse(c, http.StatusCreated, category)
}

// GET /categories
func (h *CategoryHandler) GetAllCategories(c *gin.Context) {
	categories, err := h.repo.GetAllCategories(c.Request.Context())
	if err != nil {
		ErrorResponse(c, http.StatusInternalServerError, "Error retrieving categories")
		return
	}
	SuccessResponse(c, http.StatusOK, categories)
}
