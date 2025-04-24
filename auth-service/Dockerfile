# Build stage
FROM golang:1.24.2-alpine3.21 AS builder

WORKDIR /app

RUN apk add --no-cache git ca-certificates

COPY go.mod go.sum ./
RUN go mod download

COPY . .

# Actualizar módulos
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