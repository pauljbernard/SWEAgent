# Integration Guide

This document explains how to integrate the new frontend with the existing DeepRepo backend.

## Architecture

The new frontend consists of:

1. **React Application**: A modern UI built with React, Vite, and styled-components
2. **Adapter Service**: A Flask service that translates between the React frontend and the existing Python backend

## Integration Options

### Option 1: Using the Adapter (Recommended)

The adapter approach allows the React frontend to communicate with the existing backend without modifying the backend code.

1. Start the adapter service:
   ```bash
   cd frontend
   python src/adapter.py
   ```

2. Start the React development server:
   ```bash
   cd frontend
   npm run dev
   ```

3. Access the UI at `http://localhost:53530`

### Option 2: Docker Compose

For production deployment, you can use Docker Compose to run both the frontend and the adapter:

```bash
cd frontend
docker-compose up --build
```

This will build and run both the frontend and adapter services, and expose the UI at `http://localhost:7860`.

### Option 3: Direct Backend Integration

For a more integrated approach, you could modify the existing backend to serve the React frontend directly:

1. Build the React application:
   ```bash
   cd frontend
   npm run build
   ```

2. Copy the built files to a location served by the backend:
   ```bash
   cp -r dist/* /path/to/backend/static/
   ```

3. Modify the backend to serve the React application and handle API requests.

## API Endpoints

The adapter service exposes the following API endpoints:

- `POST /api/initialize`: Initialize a repository from a URL
- `POST /api/upload`: Upload a repository as a zip file
- `POST /api/generate`: Generate a response from the AI

These endpoints correspond to the functions in `front_init_repo.py`:

- `init_repo`: Initialize a repository from a URL
- `handle_zip_upload`: Upload a repository as a zip file
- `respond`: Generate a response from the AI

## Configuration

The frontend can be configured through environment variables:

- `VITE_API_URL`: The URL of the API server (default: `/api`)
- `VITE_DEFAULT_MODEL`: The default model to use (default: `gemini-1.5-flash-8b-001`)

Create a `.env` file in the frontend directory to set these variables:

```
VITE_API_URL=http://localhost:5000/api
VITE_DEFAULT_MODEL=gemini-1.5-flash-8b-001
```