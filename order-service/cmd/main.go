package main

import (
	"context"
	"fmt"
	"log"
	"order-service/internal/config"
	"order-service/internal/handlers"
	"order-service/internal/handlers/events"
	"order-service/internal/health"
	"order-service/internal/repository"
	"order-service/internal/routes"
	"order-service/internal/services/payment"
	"order-service/pkg/database"
	"os"
	"time"

	"github.com/streadway/amqp"
)

func main() {
	cfg := config.LoadConfig()
	if len(os.Args) > 1 && os.Args[1] == "--healthcheck" {
		if err := runHealthcheck(cfg); err != nil {
			log.Print(err)
			os.Exit(1)
		}
		return
	}

	// MongoDB connection
	client, err := database.NewMongoClient(cfg.MongoDBURI)
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
		log.Printf("RabbitMQ publisher unavailable, continuing without async events: %v", err)
	}
	if eventPublisher != nil {
		defer eventPublisher.Close()
	}

	orderHandler := handlers.NewOrderHandler(orderRepo, paymentProcessor, eventPublisher)
	healthChecker := health.NewChecker("order-service", map[string]health.CheckFunc{
		"mongodb": func(ctx context.Context) error {
			healthCtx, cancel := context.WithTimeout(ctx, 5*time.Second)
			defer cancel()
			return client.Ping(healthCtx, nil)
		},
		"rabbitmq": func(ctx context.Context) error {
			conn, err := amqp.Dial(cfg.RabbitMQURI)
			if err != nil {
				return err
			}
			defer conn.Close()
			return nil
		},
	})
	healthHandler := handlers.NewHealthHandler(healthChecker)

	// Configure router
	router := routes.NewRouter(orderHandler, healthHandler, cfg)

	// Start server
	log.Printf("Server running on port %s", cfg.Port)
	if err := router.Run(":" + cfg.Port); err != nil {
		log.Fatal("Server failed to start: ", err)
	}
}

func runHealthcheck(cfg *config.Config) error {
	checker := health.NewChecker("order-service", map[string]health.CheckFunc{
		"mongodb": func(ctx context.Context) error {
			client, err := database.NewMongoClient(cfg.MongoDBURI)
			if err != nil {
				return err
			}
			defer client.Disconnect(ctx)
			return nil
		},
		"rabbitmq": func(ctx context.Context) error {
			conn, err := amqp.Dial(cfg.RabbitMQURI)
			if err != nil {
				return err
			}
			defer conn.Close()
			return nil
		},
	})

	if !checker.Healthy(context.Background()) {
		return fmt.Errorf("order-service healthcheck failed")
	}

	return nil
}
