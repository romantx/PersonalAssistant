# Stage 1: Build the Go binary
FROM golang:1.21-alpine AS builder

# Set the working directory inside the container
WORKDIR /app

# Copy go.mod and go.sum files to download dependencies
COPY go.mod go.sum ./
RUN go mod download

# Copy the rest of the source code
COPY . .

# Build the application. CGO_ENABLED=0 is important for a static binary.
# -ldflags="-w -s" strips debug information, reducing the binary size.
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-w -s" -o /auth-api ./cmd/server

# Stage 2: Create the final, minimal image
FROM alpine:latest

# Copy the static binary from the builder stage
COPY --from=builder /auth-api /auth-api

# Expose the port the server runs on
EXPOSE 8080

# The command to run the application
ENTRYPOINT ["/auth-api"]