package main

import (
	"context"
	"log"
	"product-service/internal/config"
	"product-service/internal/handlers"
	"product-service/internal/repository"
	middleware "product-service/pkg/middleware"

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
