package routes

import (
	"order-service/internal/config"
	"order-service/internal/handlers"
	"order-service/pkg/middleware"
	"time"

	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
)

func NewRouter(orderHandler *handlers.OrderHandler, healthHandler *handlers.HealthHandler, cfg *config.Config) *gin.Engine {
	router := gin.Default()

	// Middlewares
	router.Use(cors.New(cors.Config{
		AllowOrigins:     cfg.AllowedOrigins,
		AllowMethods:     []string{"GET", "POST", "PUT", "DELETE"},
		AllowHeaders:     []string{"Authorization", "Content-Type", "X-Request-ID"},
		ExposeHeaders:    []string{"Content-Length", "X-Request-ID"},
		AllowCredentials: true,
		MaxAge:           12 * time.Hour,
	}))

	router.Use(middleware.RequestID())
	router.Use(middleware.SecurityHeaders())
	router.Use(middleware.RateLimiter(cfg.RateLimit))
	router.GET("/health", healthHandler.GetHealth)

	protected := router.Group("/")
	protected.Use(middleware.AuthMiddleware(cfg.JWTSecret))
	{
		protected.POST("/orders", orderHandler.CreateOrder)
		protected.GET("/orders", orderHandler.GetAllOrders)
		protected.GET("/orders/:id", orderHandler.GetOrderByID)
	}

	return router
}
