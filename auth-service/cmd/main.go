package main

import (
	"auth-service/internal/config"
	"auth-service/internal/handlers"
	"auth-service/internal/repository"
	"auth-service/pkg/middleware"
	"context"
	"log"
	"time"

	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
	"github.com/ulule/limiter/v3"
	ginmw "github.com/ulule/limiter/v3/drivers/middleware/gin"
	"github.com/ulule/limiter/v3/drivers/store/memory"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

func main() {
	cfg := config.LoadConfig()

	// Conectar a MongoDB
	client, err := mongo.Connect(context.Background(), options.Client().ApplyURI(cfg.MongoDBURI))
	if err != nil {
		log.Fatal(err)
	}
	defer client.Disconnect(context.Background())

	db := client.Database(cfg.DBName)
	userRepo := repository.NewUserRepository(db)

	// Configurar Gin
	r := gin.Default()

	// Configurar CORS
	r.Use(cors.New(cors.Config{
		AllowOrigins:     []string{"http://localhost:3000"},
		AllowMethods:     []string{"GET", "POST"},
		AllowHeaders:     []string{"Authorization"},
		ExposeHeaders:    []string{"Content-Length"},
		AllowCredentials: true,
	}))

	// Configurar Rate Limiter
	rate := limiter.Rate{
		Period: 1 * time.Minute,
		Limit:  10,
	}
	store := memory.NewStore()
	limiterInstance := limiter.New(store, rate)
	rateLimiterMiddleware := ginmw.NewMiddleware(limiterInstance) // Variable renombrada
	r.Use(rateLimiterMiddleware)

	authHandler := handlers.NewAuthHandler(userRepo, cfg.JWTSecret)

	// Endpoints públicos
	r.POST("/auth/register", authHandler.Register)
	r.POST("/auth/login", authHandler.Login)

	// Endpoints protegidos
	authRoutes := r.Group("/users")
	authRoutes.Use(middleware.AuthMiddleware(cfg.JWTSecret)) // Middleware JWT correcto
	{
		authRoutes.GET("/:id", authHandler.GetUserByID)
	}

	r.Run(":" + cfg.Port)
}
