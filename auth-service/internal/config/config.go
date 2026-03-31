package config

import (
	"log"
	"os"
	"strings"

	"github.com/joho/godotenv"
)

type Config struct {
	MongoDBURI      string
	DBName          string
	JWTSecret       string
	GoogleClientID  string
	Port            string
	AllowedOrigins  []string
	RateLimit       string
	TokenExpiration string
}

func LoadConfig() *Config {
	if err := godotenv.Load(); err != nil {
		log.Print("Warning: No .env file found")
	}

	return &Config{
		MongoDBURI:      getEnv("MONGODB_URI", "mongodb://mongo:27017"),
		DBName:          getEnv("DB_NAME", "shop-nexus-core"),
		JWTSecret:       getEnv("JWT_SECRET", "super_secret_key_here"),
		GoogleClientID:  os.Getenv("GOOGLE_CLIENT_ID"),
		Port:            getEnv("PORT", "8000"),
		AllowedOrigins:  strings.Split(getEnv("ALLOWED_ORIGINS", "http://localhost:3000"), ","),
		RateLimit:       getEnv("RATE_LIMIT", "100-M"),
		TokenExpiration: getEnv("TOKEN_EXPIRATION", "24h"),
	}
}

// getEnv returns the configured value or a fallback when the variable is missing.
func getEnv(key, defaultValue string) string {
	value := os.Getenv(key)
	if value == "" {
		log.Printf("warning: %s not found in .env, using fallback value: %s", key, defaultValue)
		return defaultValue
	}
	return value
}
