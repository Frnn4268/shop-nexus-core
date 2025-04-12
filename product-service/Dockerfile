# Build stage
FROM golang:1.24.2-alpine3.21 AS builder

WORKDIR /app

RUN apk add --no-cache git  

COPY . .

RUN go mod download

RUN CGO_ENABLED=0 GOOS=linux go build -o product-service ./cmd/main.go

# Runtime stage
FROM alpine:latest

WORKDIR /app

COPY --from=builder /app/product-service .

COPY .env .

EXPOSE 8001

CMD ["./product-service"]