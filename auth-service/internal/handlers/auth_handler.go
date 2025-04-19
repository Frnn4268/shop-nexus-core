package handlers

import (
	"auth-service/internal/models"
	"auth-service/internal/repository"
	"auth-service/internal/utils"
	"net/http"

	"github.com/gin-gonic/gin"
	"go.mongodb.org/mongo-driver/mongo"
	"golang.org/x/crypto/bcrypt"
)

type AuthHandler struct {
	userRepo  *repository.UserRepository
	jwtSecret string
}

type CreateUserRequest struct {
	Name        string   `json:"name"`
	Email       string   `json:"email"`
	Password    string   `json:"password"`
	PhoneNumber string   `json:"phone_number"`
	Roles       []string `json:"roles"`
}

// Nueva función auxiliar en auth_handler.go
func stringToRoles(roles []string) []models.Role {
	result := make([]models.Role, len(roles))
	for i, role := range roles {
		result[i] = models.Role(role)
	}
	return result
}

func NewAuthHandler(userRepo *repository.UserRepository, jwtSecret string) *AuthHandler {
	return &AuthHandler{userRepo: userRepo, jwtSecret: jwtSecret}
}

// Register: POST /auth/register
func (h *AuthHandler) Register(c *gin.Context) {
	var req CreateUserRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Validar roles
	validRoles := map[string]bool{"user": true, "admin": true}
	for _, role := range req.Roles {
		if !validRoles[role] {
			c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid role: " + role})
			return
		}
	}

	if len(req.Roles) == 0 {
		req.Roles = []string{"user"}
	}

	hashedPassword, _ := bcrypt.GenerateFromPassword([]byte(req.Password), bcrypt.DefaultCost)

	user := models.User{
		Name:        req.Name,
		Email:       req.Email,
		Password:    string(hashedPassword),
		PhoneNumber: req.PhoneNumber,
		Roles:       stringToRoles(req.Roles),
	}

	if err := h.userRepo.CreateUser(c.Request.Context(), &user); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Error creating user"})
		return
	}

	// Respuesta con ID convertido
	c.JSON(http.StatusCreated, gin.H{
		"id":           user.ID.Hex(),
		"name":         user.Name,
		"email":        user.Email,
		"phone_number": user.PhoneNumber,
		"roles":        user.Roles,
	})
}

// Login: POST /auth/login
func (h *AuthHandler) Login(c *gin.Context) {
	var credentials struct {
		Email    string `json:"email"`
		Password string `json:"password"`
	}

	if err := c.ShouldBindJSON(&credentials); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	user, err := h.userRepo.FindUserByEmail(c.Request.Context(), credentials.Email)
	if err != nil {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid credentials"})
		return
	}

	if err := bcrypt.CompareHashAndPassword([]byte(user.Password), []byte(credentials.Password)); err != nil {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid credentials"})
		return
	}

	token, _ := utils.GenerateJWT(
		user.ID.Hex(),
		user.Email,
		utils.RolesToStringSlice(user.Roles),
		h.jwtSecret,
	)

	c.JSON(http.StatusOK, gin.H{"token": token})
}

// GetUserByID: GET /users/:id
func (h *AuthHandler) GetUserByID(c *gin.Context) {
	userID := c.Param("id")

	user, err := h.userRepo.FindUserByID(c.Request.Context(), userID)
	if err != nil {
		if err == mongo.ErrNoDocuments {
			c.JSON(http.StatusNotFound, gin.H{"error": "User not found"})
			return
		}
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Error retrieving user"})
		return
	}

	response := gin.H{
		"id":           user.ID.Hex(),
		"name":         user.Name,
		"email":        user.Email,
		"phone_number": user.PhoneNumber,
		"roles":        user.Roles,
	}

	c.JSON(http.StatusOK, response)
}
