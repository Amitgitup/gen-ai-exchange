#!/bin/bash

# Frontend Startup Script for Multi-Level Summarization System

echo "🚀 Starting Multi-Level Summarization Frontend..."
echo "================================================"

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: package.json not found. Please run this script from the frontend directory."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Error: Node.js is not installed. Please install Node.js 18+ first."
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "❌ Error: Node.js version 18+ is required. Current version: $(node -v)"
    exit 1
fi

echo "✅ Node.js version: $(node -v)"

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
    if [ $? -ne 0 ]; then
        echo "❌ Error: Failed to install dependencies"
        exit 1
    fi
    echo "✅ Dependencies installed successfully"
else
    echo "✅ Dependencies already installed"
fi

# Check if backend is running
echo "🔍 Checking backend connection..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend is running on port 8000"
elif curl -s http://localhost:8001/health > /dev/null 2>&1; then
    echo "⚠️  Backend orchestrator not available, but Server 1 is running"
else
    echo "⚠️  Warning: Backend servers not detected. Please start the backend first:"
    echo "   cd ../ && python manage_system.py start"
fi

# Create .env.local if it doesn't exist
if [ ! -f ".env.local" ]; then
    echo "📝 Creating .env.local file..."
    cat > .env.local << EOF
# Backend API URL
NEXT_PUBLIC_API_BASE=http://localhost:8000

# Alternative server URLs
NEXT_PUBLIC_SERVER1_URL=http://localhost:8001
NEXT_PUBLIC_SERVER2_URL=http://localhost:8002
NEXT_PUBLIC_SERVER3_URL=http://localhost:8003
EOF
    echo "✅ Created .env.local file"
else
    echo "✅ .env.local file already exists"
fi

echo ""
echo "🎉 Frontend setup complete!"
echo ""
echo "🚀 Starting development server..."
echo "   Frontend will be available at: http://localhost:3000"
echo "   Backend should be running at: http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the development server
npm run dev
