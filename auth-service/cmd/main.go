package main

import (
	"auth-service/internal/config"
	"auth-service/internal/handlers"
	"auth-service/internal/repository"
	"auth-service/pkg/middleware"
	"context"
	"log"

	"github.com/gin-gonic/gin"
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

	authHandler := handlers.NewAuthHandler(userRepo, cfg.JWTSecret)

	// Endpoints públicos
	r.POST("/auth/register", authHandler.Register)
	r.POST("/auth/login", authHandler.Login)

	// Endpoints protegidos
	authRoutes := r.Group("/users")
	authRoutes.Use(middleware.AuthMiddleware(cfg.JWTSecret))
	{
		authRoutes.GET("/:id", func(c *gin.Context) {
			// Implementar lógica para obtener usuario por ID
		})
	}

	r.Run(":" + cfg.Port)
}
