package models

import (
	"github.com/golang-jwt/jwt/v5"
	"go.mongodb.org/mongo-driver/bson/primitive"
)

type Role string

type AuthProvider string

const (
	RoleUser  Role = "user"
	RoleAdmin Role = "admin"

	AuthProviderLocal  AuthProvider = "local"
	AuthProviderGoogle AuthProvider = "google"
)

type User struct {
	ID           primitive.ObjectID `bson:"_id,omitempty"`
	Name         string             `bson:"name"`
	Email        string             `bson:"email"`
	PhoneNumber  string             `bson:"phone_number"`
	Password     string             `bson:"password"`
	Roles        []Role             `bson:"roles"`
	AuthProvider AuthProvider       `bson:"auth_provider,omitempty"`
	OAuthSubject string             `bson:"oauth_subject,omitempty"`
}

type JWTClaims struct {
	UserID string   `json:"user_id"`
	Email  string   `json:"email"`
	Roles  []string `json:"roles"`
	jwt.RegisteredClaims
}
