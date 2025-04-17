package utils

import (
	"net/http"

	"github.com/gin-gonic/gin"
	"go.mongodb.org/mongo-driver/bson/primitive"
)

// Validar formato de precio
func ValidatePrice(c *gin.Context, price float64) bool {
	if price <= 0 {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Price must be positive"})
		return false
	}
	return true
}

// Validar ObjectID
func ValidateObjectID(c *gin.Context, id string) (primitive.ObjectID, bool) {
	objID, err := primitive.ObjectIDFromHex(id)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid ID format"})
		return primitive.NilObjectID, false
	}
	return objID, true
}

// Validar formato de nombre
func ValidateName(c *gin.Context, name string) bool {
	if len(name) < 3 {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Name must be at least 3 characters"})
		return false
	}
	return true
}
