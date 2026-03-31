package main

import (
	"auth-service/internal/config"
	"auth-service/internal/handlers"
	"auth-service/internal/health"
	"auth-service/internal/repository"
	"auth-service/internal/routes"
	"auth-service/pkg/database"
	"context"
	"fmt"
	"log"
	"net/http"
	"os"
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

	// Connect to MongoDB.
	mongoClient, err := database.NewMongoClient(cfg.MongoDBURI)
	if err != nil {
		log.Fatal("Failed to connect to MongoDB:", err)
	}
	defer mongoClient.Disconnect(context.Background())

	// Initialize repositories and handlers.
	db := mongoClient.Database(cfg.DBName)
	userRepo := repository.NewUserRepository(db)
	authHandler := handlers.NewAuthHandler(userRepo, cfg)
	healthChecker := health.NewChecker("auth-service", map[string]health.CheckFunc{
		"mongodb": func(ctx context.Context) error {
			healthCtx, cancel := context.WithTimeout(ctx, 5*time.Second)
			defer cancel()
			return mongoClient.Ping(healthCtx, nil)
		},
	})
	healthHandler := handlers.NewHealthHandler(healthChecker)

	// Build the HTTP router.
	router := routes.NewRouter(authHandler, healthHandler, cfg)

	// Configure the HTTP server with conservative timeouts.
	srv := &http.Server{
		Addr:         ":" + cfg.Port,
		Handler:      router,
		ReadTimeout:  15 * time.Second,
		WriteTimeout: 30 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	log.Printf("Server running on port %s", cfg.Port)
	if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
		log.Fatal("Server failed:", err)
	}
}

func runHealthcheck(cfg *config.Config) error {
	checker := health.NewChecker("auth-service", map[string]health.CheckFunc{
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
		return fmt.Errorf("auth-service healthcheck failed")
	}

	return nil
}
