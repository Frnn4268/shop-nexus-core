package routes

import (
	"order-service/internal/config"
	"order-service/internal/handlers"
	"order-service/pkg/middleware"
	"time"

	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
)

func NewRouter(orderHandler *handlers.OrderHandler, cfg *config.Config) *gin.Engine {
	router := gin.Default()

	// Middlewares
	router.Use(cors.New(cors.Config{
		AllowOrigins:     cfg.AllowedOrigins,
		AllowMethods:     []string{"GET", "POST", "PUT", "DELETE"},
		AllowHeaders:     []string{"Authorization", "Content-Type"},
		ExposeHeaders:    []string{"Content-Length"},
		AllowCredentials: true,
		MaxAge:           12 * time.Hour,
	}))

	router.Use(middleware.SecurityHeaders())
	router.Use(middleware.RateLimiter(cfg.RateLimit))
	router.Use(middleware.AuthMiddleware(cfg.JWTSecret))

	// Routes
	router.POST("/orders", orderHandler.CreateOrder)
	router.GET("/orders", orderHandler.GetAllOrders)
	router.GET("/orders/:id", orderHandler.GetOrderByID)

	return router
}
