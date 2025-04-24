package config

import (
	"log"
	"os"
	"strings"

	"github.com/joho/godotenv"
)

type Config struct {
	MongoDBURI     string
	DBName         string
	JWTSecret      string
	Port           string
	AllowedOrigins []string
	RateLimit      string
}

func LoadConfig() *Config {
	if err := godotenv.Load(); err != nil {
		log.Print("Warning: No .env file found")
	}

	return &Config{
		MongoDBURI:     getEnv("MONGODB_URI", "mongodb://localhost:27017"),
		DBName:         getEnv("DB_NAME", "product_service"),
		JWTSecret:      getEnv("JWT_SECRET", "default_secret"),
		Port:           getEnv("PORT", "8001"),
		AllowedOrigins: strings.Split(getEnv("ALLOWED_ORIGINS", "http://localhost:3000"), ","),
		RateLimit:      getEnv("RATE_LIMIT", "100-M"),
	}
}

func getEnv(key, defaultValue string) string {
	value := os.Getenv(key)
	if value == "" {
		log.Printf("⚠️  %s no encontrado en .env. Usando valor por defecto: %s", key, defaultValue)
		return defaultValue
	}
	return value
}
