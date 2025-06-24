# Makefile for opendeepwiki

# Variables
IMAGE_NAME := opendeepwiki
CONTAINER_NAME := opendeepwiki_app
ENV_FILE := .env
ENV_EXAMPLE_FILE := .env.example

# Default target: Show help
.DEFAULT_GOAL := help

# Phony targets (targets that are not actual files)
.PHONY: help build run start stop logs clean prune-all env env-check setup

## -----------------------------------------------------------------------------
## General Commands
## -----------------------------------------------------------------------------

help: ## Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

## -----------------------------------------------------------------------------
## Environment Setup
## -----------------------------------------------------------------------------

env: $(ENV_EXAMPLE_FILE) ## Create .env from .env.example if .env does not exist
	@if [ ! -f $(ENV_FILE) ]; then \
		echo "Creating $(ENV_FILE) from $(ENV_EXAMPLE_FILE)..."; \
		cp $(ENV_EXAMPLE_FILE) $(ENV_FILE); \
		echo "IMPORTANT: Please fill in your API keys in $(ENV_FILE)."; \
	else \
		echo "$(ENV_FILE) already exists. Ensure it is correctly configured."; \
	fi

$(ENV_EXAMPLE_FILE):
	@echo "Creating $(ENV_EXAMPLE_FILE)..."
	@echo "# Required API Keys" > $(ENV_EXAMPLE_FILE)
	@echo "GEMINI_API_KEY=" >> $(ENV_EXAMPLE_FILE)
	@echo "" >> $(ENV_EXAMPLE_FILE)
	@echo "# Optional Langfuse Tracing (leave blank if not used)" >> $(ENV_EXAMPLE_FILE)
	@echo "LANGFUSE_PUBLIC_KEY=" >> $(ENV_EXAMPLE_FILE)
	@echo "LANGFUSE_SECRET_KEY=" >> $(ENV_EXAMPLE_FILE)
	@echo "LANGFUSE_HOST=https://cloud.langfuse.com" >> $(ENV_EXAMPLE_FILE)
	@echo "$(ENV_EXAMPLE_FILE) created. Copy to .env and fill it out, or run 'make env'."

env-check: ## Check if .env file exists
	@if [ ! -f $(ENV_FILE) ]; then \
		echo "Error: $(ENV_FILE) not found!"; \
		echo "Please create it by copying $(ENV_EXAMPLE_FILE) to $(ENV_FILE) and filling in your API keys,"; \
		echo "or run 'make env' to create a template."; \
		exit 1; \
	fi
	@echo "$(ENV_FILE) found."

## -----------------------------------------------------------------------------
## Docker Operations
## -----------------------------------------------------------------------------

build: env-check ## Build the Docker image
	@echo "Building Docker image $(IMAGE_NAME)..."
	docker build -t $(IMAGE_NAME) .

run: env-check ## Stop, remove, and run the Docker container to ensure a clean start
	@echo "Ensuring any old container is stopped and removed..."
	@docker stop $(CONTAINER_NAME) >/dev/null 2>&1 || true
	@docker rm $(CONTAINER_NAME) >/dev/null 2>&1 || true

	@echo "Starting Docker container $(CONTAINER_NAME)..."
	docker run -d --name $(CONTAINER_NAME) \
	  -p 7860:7860 \
	  -p 5050:5050 \
	  -p 8001:8001 \
	  -p 8002:8002 \
	  --env-file $(ENV_FILE) \
	  $(IMAGE_NAME)

	@echo "Container $(CONTAINER_NAME) should be running. Access UI at http://localhost:7860"

start: run ## Alias for 'run'

stop: ## Stop and remove the Docker container
	@echo "Stopping Docker container $(CONTAINER_NAME)..."
	@if [ $$(docker ps -q -f name=^$(CONTAINER_NAME)$$) ]; then \
		docker stop $(CONTAINER_NAME); \
	else \
		echo "Container $(CONTAINER_NAME) is not running."; \
	fi
	@echo "Removing Docker container $(CONTAINER_NAME) if it exists..."
	@if [ $$(docker ps -aq -f name=^$(CONTAINER_NAME)$$) ]; then \
		docker rm $(CONTAINER_NAME); \
	else \
		echo "Container $(CONTAINER_NAME) does not exist or already removed."; \
	fi

restart: ## Restart the Docker container (stop, then build and run)
	$(MAKE) stop
	$(MAKE) build
	$(MAKE) run

logs: ## Follow logs from the Docker container
	@echo "Following logs for $(CONTAINER_NAME)... (Ctrl+C to stop)"
	docker logs -f $(CONTAINER_NAME)

## -----------------------------------------------------------------------------
## Cleanup Operations
## -----------------------------------------------------------------------------

clean: stop ## Stop and remove the container, then remove the Docker image
	@echo "Removing Docker image $(IMAGE_NAME)..."
	@if $$(docker images -q $(IMAGE_NAME)); then \
		docker rmi $(IMAGE_NAME); \
	else \
		echo "Image $(IMAGE_NAME) not found."; \
	fi

prune-all: clean ## Clean everything: stop container, remove image, and prune unused Docker objects
	@echo "Pruning unused Docker volumes, networks, and dangling images..."
	docker system prune -f
	docker volume prune -f
	@echo "Full Docker prune complete."

## -----------------------------------------------------------------------------
## Convenience Targets
## -----------------------------------------------------------------------------

setup: env build run ## Setup environment, build image, and run container
	@echo "Setup complete. opendeepwiki should be accessible at http://localhost:7860"