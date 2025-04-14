package handlers

import (
	"encoding/json"
	"log"
	"net/http"
	"order-service/internal/models"
	"order-service/internal/payment"
	"order-service/internal/repository"
	"os"

	"github.com/gin-gonic/gin"
	"github.com/streadway/amqp"
)

type OrderHandler struct {
	repo *repository.OrderRepository
}

func NewOrderHandler(repo *repository.OrderRepository) *OrderHandler {
	return &OrderHandler{repo: repo}
}

// POST /orders
func (h *OrderHandler) CreateOrder(c *gin.Context) {
	var order models.Order
	if err := c.ShouldBindJSON(&order); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Calcular total
	var total float64
	for _, item := range order.Items {
		total += item.Price * float64(item.Quantity)
	}
	order.Total = total

	// Simular pago
	paymentResponse := payment.ProcessPayment(order.Total)
	if !paymentResponse.Success {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Payment failed"})
		return
	}

	order.Status = models.StatusCompleted

	if err := h.repo.CreateOrder(c.Request.Context(), &order); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Error creating order"})
		return
	}

	conn, err := amqp.Dial(os.Getenv("RABBITMQ_URI")) // Usar variable de entorno
	if err != nil {
		log.Printf("Error conectando a RabbitMQ: %v", err)
	} else {
		defer conn.Close()

		ch, err := conn.Channel()
		if err != nil {
			log.Printf("Error abriendo canal: %v", err)
		} else {
			defer ch.Close()

			body, _ := json.Marshal(order)
			err = ch.Publish(
				"",              // exchange
				"order_created", // routing key
				false,           // mandatory
				false,           // immediate
				amqp.Publishing{
					ContentType: "application/json",
					Body:        body,
				},
			)

			if err != nil {
				log.Printf("Error publicando mensaje: %v", err)
			} else {
				log.Println("Evento order_created publicado exitosamente")
			}
		}
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
