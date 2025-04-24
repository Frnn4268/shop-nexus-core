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
		Port:            getEnv("PORT", "8000"),
		AllowedOrigins:  strings.Split(getEnv("ALLOWED_ORIGINS", "http://localhost:3000"), ","),
		RateLimit:       getEnv("RATE_LIMIT", "100-M"),
		TokenExpiration: getEnv("TOKEN_EXPIRATION", "24h"),
	}
}

// Función auxiliar para valores por defecto
func getEnv(key, defaultValue string) string {
	value := os.Getenv(key)
	if value == "" {
		log.Printf("⚠️  %s no encontrado en .env. Usando valor por defecto: %s", key, defaultValue)
		return defaultValue
	}
	return value
}
