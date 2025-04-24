package main

import (
	"context"
	"log"
	"order-service/internal/config"
	"order-service/internal/handlers"
	"order-service/internal/handlers/events"
	"order-service/internal/repository"
	"order-service/internal/routes"
	"order-service/internal/services/payment"

	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

func main() {
	cfg := config.LoadConfig()

	// MongoDB Connection
	client, err := mongo.Connect(context.Background(), options.Client().ApplyURI(cfg.MongoDBURI))
	if err != nil {
		log.Fatal("Failed to connect to MongoDB: ", err)
	}
	defer client.Disconnect(context.Background())

	// Initialize components
	db := client.Database(cfg.DBName)
	orderRepo := repository.NewOrderRepository(db)
	paymentProcessor := payment.NewProcessor(0.8) // 80% success rate

	eventPublisher, err := events.NewEventPublisher(cfg.RabbitMQURI)
	if err != nil {
		log.Fatal("Failed to create event publisher: ", err)
	}
    
	defer eventPublisher.Close()

	orderHandler := handlers.NewOrderHandler(orderRepo, paymentProcessor, eventPublisher)

	// Configure router
	router := routes.NewRouter(orderHandler, cfg)

	// Start server
	log.Printf("Server running on port %s", cfg.Port)
	if err := router.Run(":" + cfg.Port); err != nil {
		log.Fatal("Server failed to start: ", err)
	}
}
