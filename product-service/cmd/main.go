package main

import (
	"context"
	"log"
	"product-service/internal/config"
	"product-service/internal/handlers"
	"product-service/internal/repository"

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
	productRepo := repository.NewProductRepository(db)

	// Configurar Gin
	r := gin.Default()
	productHandler := handlers.NewProductHandler(productRepo)

	// Endpoints de Productos
	r.GET("/products", productHandler.GetAllProducts)
	r.POST("/products", productHandler.CreateProduct)
	r.GET("/products/:id", productHandler.GetProductByID)

	// Endpoints de Categorías
	r.GET("/categories", productHandler.GetAllCategories)
	r.POST("/categories", productHandler.CreateCategory)

	r.Run(":" + cfg.Port)
}
