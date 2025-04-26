# Build stage
FROM golang:1.24.2-alpine3.21 AS builder

WORKDIR /app

# Instalar dependencias de compilación
RUN apk add --no-cache git ca-certificates

COPY go.mod go.sum ./
RUN go mod download

COPY . .

# Compilar
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-w -s" -o /order-service ./cmd/main.go

# Runtime stage (imagen mínima)
FROM alpine:3.21

WORKDIR /
COPY --from=builder /order-service .
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/

EXPOSE 8002

# Comando directo sin wait-for.sh
CMD ["./order-service"]