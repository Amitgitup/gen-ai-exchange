#!/usr/bin/env bash

# Multi-Level Summarization System Startup Script
# This script provides easy startup options for the hierarchical summarization system

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"
REQUIREMENTS_FILE="$SCRIPT_DIR/backend/requirements.txt"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Python version
check_python() {
    if command_exists python3; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        print_status "Found Python $PYTHON_VERSION"
        
        # Check if version is 3.8 or higher
        if python3 -c 'import sys; exit(0 if sys.version_info >= (3, 8) else 1)'; then
            print_success "Python version is compatible"
            return 0
        else
            print_error "Python 3.8 or higher is required"
            return 1
        fi
    else
        print_error "Python 3 is not installed"
        return 1
    fi
}

# Function to setup virtual environment
setup_venv() {
    if [ ! -d "$VENV_DIR" ]; then
        print_status "Creating virtual environment..."
        python3 -m venv "$VENV_DIR"
        print_success "Virtual environment created"
    else
        print_status "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source "$VENV_DIR/bin/activate"
    print_success "Virtual environment activated"
}

# Function to install dependencies
install_dependencies() {
    print_status "Installing dependencies..."
    
    # Upgrade pip first
    pip install --upgrade pip
    
    # Install from requirements.txt if it exists
    if [ -f "$REQUIREMENTS_FILE" ]; then
        pip install -r "$REQUIREMENTS_FILE"
        print_success "Dependencies installed from requirements.txt"
    else
        # Install core dependencies
        pip install fastapi uvicorn httpx pydantic google-generativeai faiss-cpu pypdf numpy python-dotenv
        print_success "Core dependencies installed"
    fi
}

# Function to check environment variables
check_env() {
    print_status "Checking environment configuration..."
    
    if [ -z "$GOOGLE_API_KEY" ]; then
        print_warning "GOOGLE_API_KEY environment variable not set"
        print_warning "Please set it with: export GOOGLE_API_KEY='your_api_key_here'"
        
        # Try to load from .env file
        if [ -f "$SCRIPT_DIR/backend/.env" ]; then
            print_status "Found .env file, loading environment variables..."
            export $(cat "$SCRIPT_DIR/backend/.env" | grep -v '^#' | xargs)
            print_success "Environment variables loaded from .env"
        else
            print_error "No .env file found and GOOGLE_API_KEY not set"
            return 1
        fi
    else
        print_success "GOOGLE_API_KEY is configured"
    fi
    
    return 0
}

# Function to create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    mkdir -p "$SCRIPT_DIR/backend/pdfs/raw"
    mkdir -p "$SCRIPT_DIR/backend/pdfs/summaries/L1"
    mkdir -p "$SCRIPT_DIR/backend/pdfs/summaries/L2"
    mkdir -p "$SCRIPT_DIR/backend/pdfs/summaries/L3"
    mkdir -p "$SCRIPT_DIR/experiment"
    
    print_success "Directories created"
}

# Function to start the system
start_system() {
    print_status "Starting multi-level summarization system..."
    
    # Change to script directory
    cd "$SCRIPT_DIR"
    
    # Start the system using the management script
    python manage_system.py start
    
    if [ $? -eq 0 ]; then
        print_success "System started successfully!"
        print_status "Orchestrator available at: http://localhost:8000"
        print_status "Server 1 available at: http://localhost:8001"
        print_status "Server 2 available at: http://localhost:8002"
        print_status "Server 3 available at: http://localhost:8003"
        print_status ""
        print_status "Use 'python manage_system.py monitor' to monitor the system"
        print_status "Use 'python manage_system.py stop' to stop the system"
    else
        print_error "Failed to start system"
        return 1
    fi
}

# Function to show usage
show_usage() {
    echo "Multi-Level Summarization System Startup Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --setup-only    Only setup environment, don't start system"
    echo "  --no-venv       Don't use virtual environment"
    echo "  --help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                    # Full setup and start"
    echo "  $0 --setup-only       # Only setup environment"
    echo "  $0 --no-venv          # Start without virtual environment"
}

# Main function
main() {
    local setup_only=false
    local no_venv=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --setup-only)
                setup_only=true
                shift
                ;;
            --no-venv)
                no_venv=true
                shift
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    print_status "Starting Multi-Level Summarization System Setup..."
    echo ""
    
    # Check Python
    if ! check_python; then
        exit 1
    fi
    
    # Setup virtual environment (unless disabled)
    if [ "$no_venv" = false ]; then
        setup_venv
    else
        print_warning "Skipping virtual environment setup"
    fi
    
    # Install dependencies
    install_dependencies
    
    # Check environment
    if ! check_env; then
        exit 1
    fi
    
    # Create directories
    create_directories
    
    print_success "Setup completed successfully!"
    echo ""
    
    # Start system unless setup-only mode
    if [ "$setup_only" = false ]; then
        start_system
    else
        print_status "Setup completed. Run '$0' to start the system."
    fi
}

# Run main function with all arguments
main "$@"
