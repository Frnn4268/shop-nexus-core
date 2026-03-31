package handlers

import (
	"context"
	"log"
	"net/http"
	"order-service/internal/handlers/events"
	"order-service/internal/models"
	"order-service/internal/repository"
	"order-service/internal/services/payment"

	"github.com/gin-gonic/gin"
	"github.com/golang-jwt/jwt"
	"go.mongodb.org/mongo-driver/bson/primitive"
)

type orderStore interface {
	CreateOrder(ctx context.Context, order *models.Order) error
	GetAllOrders(ctx context.Context) ([]models.Order, error)
	GetOrderByID(ctx context.Context, id string) (*models.Order, error)
}

type paymentProcessor interface {
	Process(amount float64) payment.Response
}

type orderEventPublisher interface {
	PublishOrderCreated(order interface{}) error
}

type OrderHandler struct {
	repo           orderStore
	paymentService paymentProcessor
	eventPublisher orderEventPublisher
}

func NewOrderHandler(
	repo *repository.OrderRepository,
	paymentService *payment.Processor,
	eventPublisher *events.EventPublisher,
) *OrderHandler {
	return NewOrderHandlerWithDependencies(repo, paymentService, eventPublisher)
}

func NewOrderHandlerWithDependencies(
	repo orderStore,
	paymentService paymentProcessor,
	eventPublisher orderEventPublisher,
) *OrderHandler {
	return &OrderHandler{
		repo:           repo,
		paymentService: paymentService,
		eventPublisher: eventPublisher,
	}
}

// POST /orders
func (h *OrderHandler) CreateOrder(c *gin.Context) {
	var order models.Order
	if err := c.ShouldBindJSON(&order); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	claims, exists := c.Get("claims")
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "User not authenticated"})
		return
	}

	claimsMap, ok := claims.(jwt.MapClaims)
	if !ok {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Invalid token claims"})
		return
	}

	userIDValue, ok := claimsMap["user_id"].(string)
	if !ok || userIDValue == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid user ID in token"})
		return
	}

	userID, err := primitive.ObjectIDFromHex(userIDValue)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid user ID in token"})
		return
	}

	order.UserID = userID

	// Calcular total (se mantiene)
	var total float64
	for _, item := range order.Items {
		total += item.Price * float64(item.Quantity)
	}
	order.Total = total

	// Simular pago (se mantiene)
	paymentResponse := h.paymentService.Process(order.Total)
	if !paymentResponse.Success {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Payment failed"})
		return
	}

	order.Status = models.StatusCompleted

	if err := h.repo.CreateOrder(c.Request.Context(), &order); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Error creating order"})
		return
	}

	requestID := c.GetString("requestID")
	publishedEvent := events.NewOrderCreatedEvent(order, requestID)

	if h.eventPublisher != nil {
		if err := h.eventPublisher.PublishOrderCreated(publishedEvent); err != nil {
			log.Printf("Failed to publish order.created event for order %s with request ID %s: %v", order.ID.Hex(), requestID, err)
		} else {
			log.Printf("Published order.created event for order %s with request ID %s", order.ID.Hex(), requestID)
		}
	} else {
		log.Printf("RabbitMQ publisher unavailable, skipping order.created event for order %s with request ID %s", order.ID.Hex(), requestID)
	}

	c.JSON(http.StatusCreated, order)
}

// GET /orders
func (h *OrderHandler) GetAllOrders(c *gin.Context) {
	orders, err := h.repo.GetAllOrders(c.Request.Context())
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Error retrieving orders"})
		return
	}
	c.JSON(http.StatusOK, orders)
}

// GET /orders/:id
func (h *OrderHandler) GetOrderByID(c *gin.Context) {
	order, err := h.repo.GetOrderByID(c.Request.Context(), c.Param("id"))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Order not found"})
		return
	}
	c.JSON(http.StatusOK, order)
}
