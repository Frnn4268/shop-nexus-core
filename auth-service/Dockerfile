# Build stage
FROM golang:1.24.2-alpine3.21 AS builder

WORKDIR /app

RUN apk add --no-cache git  

COPY . .

RUN go mod download

RUN CGO_ENABLED=0 GOOS=linux go build -o auth-service ./cmd/main.go

# Runtime stage
FROM alpine:latest

WORKDIR /app

COPY --from=builder /app/auth-service .

COPY .env .

EXPOSE 8000

CMD ["./auth-service"]