package main

import (
	"auth-service/internal/config"
	"auth-service/internal/handlers"
	"auth-service/internal/repository"
	"auth-service/internal/routes"
	"auth-service/pkg/database"
	"context"
	"log"
	"net/http"
	"time"
)

func main() {
	cfg := config.LoadConfig()

	// Conexión a MongoDB
	mongoClient, err := database.NewMongoClient(cfg.MongoDBURI)
	if err != nil {
		log.Fatal("Failed to connect to MongoDB:", err)
	}
	defer mongoClient.Disconnect(context.Background())

	// Inicializar repositorios y handlers
	db := mongoClient.Database(cfg.DBName)
	userRepo := repository.NewUserRepository(db)
	authHandler := handlers.NewAuthHandler(userRepo, cfg)

	// Configurar router
	router := routes.NewRouter(authHandler, cfg)

	// Configurar servidor HTTP con timeout
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
