# Build stage
FROM golang:1.24.2-alpine3.21 AS builder

WORKDIR /app

# Instalar dependencias necesarias para el wait-for
RUN apk add --no-cache git ca-certificates build-base bash curl

COPY go.mod go.sum ./
RUN go mod download

COPY . .

# Compilar
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-w -s" -o /order-service ./cmd/main.go

# Runtime stage (usar alpine en lugar de distroless para tener shell)
FROM alpine:3.21

WORKDIR /
RUN apk add --no-cache bash curl

# Copiar script de espera
COPY --from=builder /app/scripts/wait-for.sh .
COPY --from=builder /order-service .
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/

EXPOSE 8002

# Esperar a RabbitMQ y Mongo antes de iniciar
CMD ["/bin/bash", "-c", "./wait-for.sh rabbitmq:5672 -- ./order-service"]