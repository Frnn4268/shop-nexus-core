# Build stage
FROM golang:1.24.2-alpine3.21 AS builder

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY . .

RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-w -s" -o /product-service ./cmd/main.go

# Runtime stage
FROM gcr.io/distroless/static-debian12

WORKDIR /
COPY --from=builder /product-service /product-service
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/

EXPOSE 8001
USER nonroot:nonroot

CMD ["/product-service"]