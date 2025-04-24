FROM golang:1.24.2-alpine3.21 AS builder

WORKDIR /app

RUN apk add --no-cache git ca-certificates

COPY go.mod go.sum ./
RUN go mod download

COPY . .

# Instalar dependencias de Swagger
RUN go install github.com/swaggo/swag/cmd/swag@v1.16.3
RUN swag init -g ./cmd/main.go -o ./api/docs

# Actualizar módulos
RUN go get -u github.com/swaggo/gin-swagger@v1.6.0
RUN go get -u github.com/swaggo/files@v1.0.1
RUN go mod tidy

# Compilar
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-w -s" -o /auth-service ./cmd/main.go

# Runtime stage
FROM gcr.io/distroless/static-debian12
WORKDIR /
COPY --from=builder /auth-service /auth-service
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
EXPOSE 8000
USER nonroot:nonroot
CMD ["/auth-service"]