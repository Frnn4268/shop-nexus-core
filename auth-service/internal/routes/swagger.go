package routes

import (
	"auth-service/api/docs"

	"github.com/gin-gonic/gin"
	ginSwagger "github.com/swaggo/gin-swagger"
	"github.com/swaggo/gin-swagger/swaggerFiles"
)

func SetupSwagger(r *gin.Engine) {
	docs.SwaggerInfo.Host = "localhost:8000"
	r.GET("/swagger/*any", ginSwagger.WrapHandler(swaggerFiles.Handler))
}
