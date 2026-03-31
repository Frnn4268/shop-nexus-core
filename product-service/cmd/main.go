package main

import (
	"context"
	"fmt"
	"log"
	"os"
	"product-service/internal/config"
	"product-service/internal/handlers"
	"product-service/internal/health"
	"product-service/internal/repository"
	"product-service/internal/routes"
	"product-service/pkg/database"
	"time"
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

	// Connect to MongoDB using the shared client helper.
	client, err := database.NewMongoClient(cfg.MongoDBURI)
	if err != nil {
		log.Fatal("Failed to connect to MongoDB:", err)
	}
	defer client.Disconnect(context.Background())

	db := client.Database(cfg.DBName)
	productRepo := repository.NewProductRepository(db)

	productHandler := handlers.NewProductHandler(productRepo)
	healthChecker := health.NewChecker("product-service", map[string]health.CheckFunc{
		"mongodb": func(ctx context.Context) error {
			healthCtx, cancel := context.WithTimeout(ctx, 5*time.Second)
			defer cancel()
			return client.Ping(healthCtx, nil)
		},
	})
	healthHandler := handlers.NewHealthHandler(healthChecker)
	router := routes.NewRouter(productHandler, healthHandler, cfg)

	if err := router.Run(":" + cfg.Port); err != nil {
		log.Fatal("Failed to start product-service:", err)
	}
}

func runHealthcheck(cfg *config.Config) error {
	checker := health.NewChecker("product-service", map[string]health.CheckFunc{
		"mongodb": func(ctx context.Context) error {
			client, err := database.NewMongoClient(cfg.MongoDBURI)
			if err != nil {
				return err
			}
			defer client.Disconnect(ctx)
			return nil
		},
	})

	if !checker.Healthy(context.Background()) {
		return fmt.Errorf("product-service healthcheck failed")
	}

	return nil
}
