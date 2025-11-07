.PHONY: build clean install build-all help

# Default target
all: build

# Build for current platform
build:
	go build -o letta-schedules

# Build for all platforms
build-all:
	GOOS=darwin GOARCH=amd64 go build -o dist/letta-schedules-darwin-amd64
	GOOS=darwin GOARCH=arm64 go build -o dist/letta-schedules-darwin-arm64
	GOOS=linux GOARCH=amd64 go build -o dist/letta-schedules-linux-amd64
	GOOS=linux GOARCH=arm64 go build -o dist/letta-schedules-linux-arm64
	GOOS=windows GOARCH=amd64 go build -o dist/letta-schedules-windows-amd64.exe

# Install to /usr/local/bin
install: build
	sudo mv letta-schedules /usr/local/bin/

# Clean build artifacts
clean:
	rm -f letta-schedules
	rm -rf dist/

# Download dependencies
deps:
	go mod download
	go mod tidy

# Run tests
test:
	go test ./...

# Show help
help:
	@echo "Available targets:"
	@echo "  build      - Build for current platform"
	@echo "  build-all  - Build for all platforms (creates dist/ directory)"
	@echo "  install    - Build and install to /usr/local/bin"
	@echo "  clean      - Remove build artifacts"
	@echo "  deps       - Download and tidy dependencies"
	@echo "  test       - Run tests"
	@echo "  help       - Show this help message"
