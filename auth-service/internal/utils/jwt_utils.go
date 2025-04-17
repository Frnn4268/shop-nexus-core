package utils

import (
	"auth-service/internal/models"
	"time"

	"auth-service/pkg/middleware"

	"github.com/golang-jwt/jwt/v5"
)

type CustomClaims struct {
	UserID string   `json:"user_id"`
	Email  string   `json:"email"`
	Roles  []string `json:"roles"`
	jwt.RegisteredClaims
}

func GenerateJWT(userID, email string, roles []string, secret string) (string, error) {
	claims := middleware.CustomClaims{ // Usa la estructura del middleware
		UserID: userID,
		Roles:  roles,
		RegisteredClaims: jwt.RegisteredClaims{
			ExpiresAt: jwt.NewNumericDate(time.Now().Add(24 * time.Hour)),
		},
	}

	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	return token.SignedString([]byte(secret))
}

func RolesToStringSlice(roles []models.Role) []string {
	strRoles := make([]string, len(roles))
	for i, role := range roles {
		strRoles[i] = string(role)
	}
	return strRoles
}
