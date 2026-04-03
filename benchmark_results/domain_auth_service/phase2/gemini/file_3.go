package main

import (
	"log"
	"net/http"

	"github.com/gorilla/mux"
	"github.com/your-username/auth-api/internal/handler"
)

func main() {
	// Create a new router
	r := mux.NewRouter()

	// Register handlers for the paths defined in the OpenAPI spec
	// The .Methods("POST") ensures these handlers only respond to POST requests.
	r.HandleFunc("/login", handler.LoginHandler).Methods(http.MethodPost)
	r.HandleFunc("/register", handler.RegisterHandler).Methods(http.MethodPost)

	// Define the server address
	port := ":8080"
	log.Printf("Starting Auth API server on %s", port)

	// Start the HTTP server
	// log.Fatal will log any error and exit the application if the server fails to start
	if err := http.ListenAndServe(port, r); err != nil {
		log.Fatal(err)
	}
}