package routes

import (
	"auth-service/internal/config"
	"auth-service/internal/handlers"
	"auth-service/pkg/middleware"
	"time"

	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
)

func NewRouter(authHandler *handlers.AuthHandler, cfg *config.Config) *gin.Engine {
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

	// Public routes
	public := router.Group("/auth")
	{
		public.POST("/register", authHandler.Register)
		public.POST("/login", authHandler.Login)
	}

	// Protected routes
	protected := router.Group("/users")
	protected.Use(middleware.AuthMiddleware(cfg.JWTSecret))
	{
		protected.GET("/:id", authHandler.GetUserByID)
	}

	return router
}
