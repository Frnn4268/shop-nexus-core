package handlers

import (
	"auth-service/internal/config"
	"auth-service/internal/models"
	"auth-service/internal/repository"
	"auth-service/internal/services"
	utils "auth-service/internal/utils/jwt"
	"context"
	"log"
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
	"go.mongodb.org/mongo-driver/bson/primitive"
	"go.mongodb.org/mongo-driver/mongo"
	"golang.org/x/crypto/bcrypt"
)

type userStore interface {
	CreateUser(ctx context.Context, user *models.User) error
	FindUserByEmail(ctx context.Context, email string) (*models.User, error)
	FindUserByID(ctx context.Context, id string) (*models.User, error)
	UpdateGoogleIdentity(ctx context.Context, userID primitive.ObjectID, subject string, name string) (*models.User, error)
}

type AuthHandler struct {
	userRepo       userStore
	jwtSecret      string
	tokenTTL       time.Duration
	googleVerifier services.GoogleVerifier
}

type CreateUserRequest struct {
	Name        string   `json:"name" binding:"required,min=2,max=100"`
	Email       string   `json:"email" binding:"required,email"`
	Password    string   `json:"password" binding:"required,min=8"`
	PhoneNumber string   `json:"phone_number" binding:"omitempty,min=7,max=20"`
	Roles       []string `json:"roles"`
}

type GoogleLoginRequest struct {
	IDToken string `json:"id_token" binding:"required"`
}

// stringToRoles converts external role names into the internal enum type.
func stringToRoles(roles []string) []models.Role {
	result := make([]models.Role, len(roles))
	for i, role := range roles {
		result[i] = models.Role(role)
	}
	return result
}

func NewAuthHandler(userRepo *repository.UserRepository, cfg *config.Config) *AuthHandler {
	tokenTTL, err := time.ParseDuration(cfg.TokenExpiration)
	if err != nil {
		log.Printf("invalid TOKEN_EXPIRATION %q, using 24h fallback", cfg.TokenExpiration)
		tokenTTL = 24 * time.Hour
	}

	return NewAuthHandlerWithDependencies(
		userRepo,
		cfg.JWTSecret,
		tokenTTL,
		services.NewGoogleVerifier(cfg.GoogleClientID),
	)
}

func NewAuthHandlerWithDependencies(userRepo userStore, jwtSecret string, tokenTTL time.Duration, googleVerifier services.GoogleVerifier) *AuthHandler {
	return &AuthHandler{
		userRepo:       userRepo,
		jwtSecret:      jwtSecret,
		tokenTTL:       tokenTTL,
		googleVerifier: googleVerifier,
	}
}

// Register: POST /auth/register
func (h *AuthHandler) Register(c *gin.Context) {
	var req CreateUserRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Validate requested roles.
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

	// Check whether the email is already registered.
	existingUser, err := h.userRepo.FindUserByEmail(c.Request.Context(), req.Email)
	if err != nil && err != mongo.ErrNoDocuments {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to validate email uniqueness"})
		return
	}
	if existingUser != nil {
		c.JSON(http.StatusConflict, gin.H{"error": "Email is already registered"})
		return
	}

	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(req.Password), bcrypt.DefaultCost)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to prepare credentials"})
		return
	}

	user := models.User{
		Name:         req.Name,
		Email:        req.Email,
		Password:     string(hashedPassword),
		PhoneNumber:  req.PhoneNumber,
		Roles:        stringToRoles(req.Roles),
		AuthProvider: models.AuthProviderLocal,
	}

	// Handle duplicate inserts defensively in case another request won the race.
	if err := h.userRepo.CreateUser(c.Request.Context(), &user); err != nil {
		if isDuplicateKeyError(err) {
			c.JSON(http.StatusConflict, gin.H{"error": "Email is already registered"})
			return
		}
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to create user"})
		return
	}

	c.JSON(http.StatusCreated, gin.H{
		"id":           user.ID.Hex(),
		"name":         user.Name,
		"email":        user.Email,
		"phone_number": user.PhoneNumber,
		"roles":        user.Roles,
	})
}

// isDuplicateKeyError detects duplicate-key violations returned by MongoDB.
func isDuplicateKeyError(err error) bool {
	if we, ok := err.(mongo.WriteException); ok {
		for _, e := range we.WriteErrors {
			if e.Code == 11000 {
				return true
			}
		}
	}
	return false
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
	if err != nil || user == nil {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid credentials"})
		return
	}

	if err := bcrypt.CompareHashAndPassword([]byte(user.Password), []byte(credentials.Password)); err != nil {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid credentials"})
		return
	}

	token, err := h.issueToken(user)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Error generating token"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"token": token})
}

// LoginWithGoogle: POST /auth/google
func (h *AuthHandler) LoginWithGoogle(c *gin.Context) {
	if h.googleVerifier == nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"error": "Google OAuth is not configured"})
		return
	}

	var req GoogleLoginRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	identity, err := h.googleVerifier.VerifyIDToken(c.Request.Context(), req.IDToken)
	if err != nil {
		c.JSON(http.StatusUnauthorized, gin.H{"error": err.Error()})
		return
	}

	user, err := h.userRepo.FindUserByEmail(c.Request.Context(), identity.Email)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to retrieve user"})
		return
	}

	switch {
	case user == nil:
		user = &models.User{
			Name:         identity.Name,
			Email:        identity.Email,
			Roles:        []models.Role{models.RoleUser},
			AuthProvider: models.AuthProviderGoogle,
			OAuthSubject: identity.Subject,
		}
		if err := h.userRepo.CreateUser(c.Request.Context(), user); err != nil {
			if isDuplicateKeyError(err) {
				c.JSON(http.StatusConflict, gin.H{"error": "Email is already registered"})
				return
			}
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to create Google user"})
			return
		}
	case user.AuthProvider == models.AuthProviderLocal || user.AuthProvider == "":
		c.JSON(http.StatusConflict, gin.H{"error": "An account with this email already exists with password login"})
		return
	case user.AuthProvider == models.AuthProviderGoogle:
		if user.OAuthSubject != "" && user.OAuthSubject != identity.Subject {
			c.JSON(http.StatusConflict, gin.H{"error": "Google account subject does not match the stored identity"})
			return
		}
		updatedUser, err := h.userRepo.UpdateGoogleIdentity(c.Request.Context(), user.ID, identity.Subject, identity.Name)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to refresh Google user profile"})
			return
		}
		user = updatedUser
	default:
		c.JSON(http.StatusConflict, gin.H{"error": "Unsupported auth provider for this account"})
		return
	}

	token, err := h.issueToken(user)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Error generating token"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"token": token,
		"user": gin.H{
			"id":    user.ID.Hex(),
			"name":  user.Name,
			"email": user.Email,
			"roles": user.Roles,
		},
	})
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

func (h *AuthHandler) issueToken(user *models.User) (string, error) {
	return utils.GenerateJWTWithTTL(
		user.ID.Hex(),
		user.Email,
		utils.RolesToStringSlice(user.Roles),
		h.jwtSecret,
		h.tokenTTL,
	)
}
