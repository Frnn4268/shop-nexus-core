package handlers

import (
	"net/http"
	"order-service/internal/health"

	"github.com/gin-gonic/gin"
)

type HealthHandler struct {
	checker *health.Checker
}

func NewHealthHandler(checker *health.Checker) *HealthHandler {
	return &HealthHandler{checker: checker}
}

func (h *HealthHandler) GetHealth(c *gin.Context) {
	result := h.checker.Check(c.Request.Context())
	statusCode := http.StatusOK
	if result.Status != "ok" {
		statusCode = http.StatusServiceUnavailable
	}

	c.JSON(statusCode, result)
}
