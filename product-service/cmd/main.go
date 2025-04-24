package main

import (
	"context"
	"log"
	"product-service/internal/config"
	"product-service/internal/handlers"
	"product-service/internal/repository"
	"product-service/pkg/database"
	middleware "product-service/pkg/middleware"

	"github.com/gin-gonic/gin"
)

func main() {
	cfg := config.LoadConfig()

	// Conexión a MongoDB usando el nuevo cliente
	client, err := database.NewMongoClient(cfg.MongoDBURI)
	if err != nil {
		log.Fatal("Error conectando a MongoDB:", err)
	}
	defer client.Disconnect(context.Background())

	db := client.Database(cfg.DBName)
	productRepo := repository.NewProductRepository(db)

	r := gin.Default()
	r.Use(middleware.AuthMiddleware(cfg.JWTSecret))

	productHandler := handlers.NewProductHandler(productRepo)

	// Productos
	r.GET("/products", productHandler.GetAllProducts)
	r.GET("/products/:id", productHandler.GetProductByID)
	r.POST("/products", productHandler.CreateProduct)
	r.PUT("/products/:id", productHandler.UpdateProduct)
	r.DELETE("/products/:id", productHandler.DeleteProduct)

	// Categorías
	r.GET("/categories", productHandler.GetAllCategories)
	r.POST("/categories", productHandler.CreateCategory)

	r.Run(":" + cfg.Port)
}
