package handlers

import "github.com/gin-gonic/gin"

type Response struct {
	Status  int         `json:"status"`
	Message string      `json:"message"`
	Data    interface{} `json:"data,omitempty"`
	Error   string      `json:"error,omitempty"`
}

func SuccessResponse(c *gin.Context, status int, data interface{}) {
	c.JSON(status, Response{
		Status:  status,
		Message: "success",
		Data:    data,
	})
}

func ErrorResponse(c *gin.Context, status int, errorMsg string) {
	c.JSON(status, Response{
		Status:  status,
		Message: "error",
		Error:   errorMsg,
	})
}
