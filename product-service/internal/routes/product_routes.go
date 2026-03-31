package routes

import (
	"product-service/internal/config"
	"product-service/internal/handlers"
	"product-service/pkg/middleware"
	"time"

	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
)

func NewRouter(productHandler *handlers.ProductHandler, healthHandler *handlers.HealthHandler, cfg *config.Config) *gin.Engine {
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

	// Public routes
	router.GET("/health", healthHandler.GetHealth)

	public := router.Group("/products")
	{
		public.GET("", productHandler.GetAllProducts)
		public.GET("/:id", productHandler.GetProductByID)
	}

	// Protected routes
	protected := router.Group("/")
	protected.Use(middleware.AuthMiddleware(cfg.JWTSecret))
	{
		protected.POST("/products", productHandler.CreateProduct)
		protected.PUT("/products/:id", productHandler.UpdateProduct)
		protected.DELETE("/products/:id", productHandler.DeleteProduct)

		// Categories
		protected.GET("/categories", productHandler.GetAllCategories)
		protected.POST("/categories", productHandler.CreateCategory)
	}

	return router
}
