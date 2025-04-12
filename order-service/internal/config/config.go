package config

import (
	"log"
	"os"

	"github.com/joho/godotenv"
)

type Config struct {
	MongoDBURI string
	DBName     string
	Port       string
}

func LoadConfig() *Config {
	// Cargar variables de entorno desde .env
	if err := godotenv.Load(); err != nil {
		log.Fatal("Error loading .env file")
	}

	return &Config{
		MongoDBURI: os.Getenv("MONGODB_URI"),
		DBName:     os.Getenv("DB_NAME"),
		Port:       os.Getenv("PORT"),
	}
}
