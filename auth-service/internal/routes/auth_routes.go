package routes

import (
	"auth-service/internal/config"
	"auth-service/internal/handlers"
	"auth-service/pkg/middleware"
	"time"

	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
)

func NewRouter(authHandler *handlers.AuthHandler, healthHandler *handlers.HealthHandler, cfg *config.Config) *gin.Engine {
	router := gin.Default()

	// CORS configuration.
	router.Use(cors.New(cors.Config{
		AllowOrigins:     cfg.AllowedOrigins,
		AllowMethods:     []string{"GET", "POST", "PUT", "DELETE"},
		AllowHeaders:     []string{"Authorization", "Content-Type", "X-Request-ID"},
		ExposeHeaders:    []string{"Content-Length", "X-Request-ID"},
		AllowCredentials: true,
		MaxAge:           12 * time.Hour,
	}))

	router.Use(middleware.RequestID())

	// Security middleware.
	router.Use(middleware.SecurityHeaders())

	// Rate limiter configured from environment variables.
	router.Use(middleware.RateLimiter(cfg.RateLimit))

	// Public routes.
	router.GET("/health", healthHandler.GetHealth)

	public := router.Group("/auth")
	{
		public.POST("/register", authHandler.Register)
		public.POST("/login", authHandler.Login)
		public.POST("/google", authHandler.LoginWithGoogle)
	}

	// Protected routes.
	protected := router.Group("/users")
	protected.Use(middleware.AuthMiddleware(cfg.JWTSecret))
	{
		protected.GET("/:id", authHandler.GetUserByID)
	}

	return router
}
