#!/bin/bash

# Start the Flask adapter in the background
echo "Starting Flask adapter..."
python src/adapter.py &
ADAPTER_PID=$!

# Start the Vite development server
echo "Starting Vite development server..."
npm run dev

# When Vite is stopped, also stop the Flask adapter
kill $ADAPTER_PID