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

	// Configuración CORS
	router.Use(cors.New(cors.Config{
		AllowOrigins:     cfg.AllowedOrigins, // Ahora existe en Config
		AllowMethods:     []string{"GET", "POST", "PUT", "DELETE"},
		AllowHeaders:     []string{"Authorization", "Content-Type"},
		ExposeHeaders:    []string{"Content-Length"},
		AllowCredentials: true,
		MaxAge:           12 * time.Hour,
	}))

	// Middlewares de seguridad
	router.Use(middleware.SecurityHeaders())

	// Rate Limiter configurado desde variables de entorno
	router.Use(middleware.RateLimiter(cfg.RateLimit)) // Middleware implementado

	// Rutas públicas
	public := router.Group("/auth")
	{
		public.POST("/register", authHandler.Register)
		public.POST("/login", authHandler.Login)
	}

	// Rutas protegidas
	protected := router.Group("/users")
	protected.Use(middleware.AuthMiddleware(cfg.JWTSecret))
	{
		protected.GET("/:id", authHandler.GetUserByID)
	}

	return router
}
