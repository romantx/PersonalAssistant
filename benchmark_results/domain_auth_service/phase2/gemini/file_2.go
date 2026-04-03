package handler

import (
	"net/http"
)

// LoginHandler handles the /login endpoint.
// It responds with a 200 OK status as per the OpenAPI spec.
func LoginHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write([]byte(`{"message": "Login successful"}`))
}

// RegisterHandler handles the /register endpoint.
// It responds with a 201 Created status as per the OpenAPI spec.
func RegisterHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	w.Write([]byte(`{"message": "User registered successfully"}`))
}