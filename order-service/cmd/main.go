package main

import (
	"context"
	"log"
	"order-service/internal/config"
	"order-service/internal/handlers"
	"order-service/internal/repository"
	middleware "order-service/pkg/middleware"

	"github.com/gin-gonic/gin"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

func main() {
	cfg := config.LoadConfig()

	client, err := mongo.Connect(context.Background(), options.Client().ApplyURI(cfg.MongoDBURI))
	if err != nil {
		log.Fatal(err)
	}
	defer client.Disconnect(context.Background())

	db := client.Database(cfg.DBName)
	orderRepo := repository.NewOrderRepository(db)

	r := gin.Default()

	// Middleware de autenticación global para todas las rutas
	r.Use(middleware.AuthMiddleware(cfg.JWTSecret))

	orderHandler := handlers.NewOrderHandler(orderRepo)

	// Endpoints protegidos
	r.POST("/orders", orderHandler.CreateOrder)
	r.GET("/orders", orderHandler.GetAllOrders)
	r.GET("/orders/:id", orderHandler.GetOrderByID)

	r.Run(":" + cfg.Port)
}
