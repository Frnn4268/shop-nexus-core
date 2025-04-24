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
	RabbitMQURI    string
}

func LoadConfig() *Config {
	if err := godotenv.Load(); err != nil {
		log.Print("Warning: No .env file found")
	}

	return &Config{
		MongoDBURI:     getEnv("MONGODB_URI", "mongodb://localhost:27017"),
		DBName:         getEnv("DB_NAME", "order_service"),
		JWTSecret:      getEnv("JWT_SECRET", "default_secret"),
		Port:           getEnv("PORT", "8002"),
		AllowedOrigins: strings.Split(getEnv("ALLOWED_ORIGINS", "http://localhost:3000"), ","),
		RateLimit:      getEnv("RATE_LIMIT", "100-M"),
		RabbitMQURI:    getEnv("RABBITMQ_URI", "amqp://guest:guest@localhost:5672/"),
	}
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}
