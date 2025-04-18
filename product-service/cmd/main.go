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
	productHandler := handlers.NewProductHandler(productRepo)

	// Grupo de rutas protegidas
	authRoutes := r.Group("/")
	authRoutes.Use(middleware.AuthMiddleware(cfg.JWTSecret))

	// Productos
	authRoutes.GET("/products", productHandler.GetAllProducts)
	authRoutes.POST("/products", productHandler.CreateProduct)
	authRoutes.PUT("/products/:id", productHandler.UpdateProduct)
	authRoutes.DELETE("/products/:id", productHandler.DeleteProduct)

	// Categorías
	authRoutes.GET("/categories", productHandler.GetAllCategories)
	authRoutes.POST("/categories", productHandler.CreateCategory)

	r.Run(":" + cfg.Port)
}
