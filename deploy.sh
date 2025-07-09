#!/bin/bash

# AI Credit Aggregator - One-Click Deployment Script
# This script sets up and deploys the complete AI Credit Aggregator application

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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
        PYTHON_CMD="python3"
    elif command_exists python; then
        PYTHON_CMD="python"
    else
        print_error "Python is not installed. Please install Python 3.7+ and try again."
        exit 1
    fi

    # Check Python version
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 7 ]); then
        print_error "Python 3.7+ is required. Found: $PYTHON_VERSION"
        exit 1
    fi

    print_success "Python $PYTHON_VERSION detected"
}

# Function to setup virtual environment
setup_venv() {
    print_status "Setting up Python virtual environment..."
    
    cd backend
    
    if [ ! -d "venv" ]; then
        $PYTHON_CMD -m venv venv
        print_success "Virtual environment created"
    else
        print_warning "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        source venv/Scripts/activate
    else
        source venv/bin/activate
    fi
    
    print_success "Virtual environment activated"
}

# Function to install dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install requirements
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        print_success "Dependencies installed successfully"
    else
        print_error "requirements.txt not found"
        exit 1
    fi
}

# Function to validate directory structure
validate_structure() {
    print_status "Validating project structure..."
    
    # Check if we're in the right directory
    if [ ! -f "deploy.sh" ]; then
        print_error "Please run this script from the ai-aggregator root directory"
        exit 1
    fi
    
    # Check required directories
    REQUIRED_DIRS=("backend" "frontend" "models" "prompts")
    for dir in "${REQUIRED_DIRS[@]}"; do
        if [ ! -d "$dir" ]; then
            print_error "Required directory '$dir' not found"
            exit 1
        fi
    done
    
    # Check required files
    if [ ! -f "backend/app.py" ]; then
        print_error "Backend application file 'backend/app.py' not found"
        exit 1
    fi
    
    if [ ! -f "frontend/index.html" ]; then
        print_error "Frontend file 'frontend/index.html' not found"
        exit 1
    fi
    
    print_success "Project structure validated"
}

# Function to check for sample data
check_sample_data() {
    print_status "Checking sample data..."
    
    # Check for model files
    MODEL_COUNT=$(find models -name "*.json" 2>/dev/null | wc -l)
    if [ "$MODEL_COUNT" -eq 0 ]; then
        print_warning "No model configuration files found in models/ directory"
        print_warning "The application will start with no models available"
    else
        print_success "Found $MODEL_COUNT model configuration(s)"
    fi
    
    # Check for prompt files
    PROMPT_COUNT=$(find prompts -name "*.jsonl" 2>/dev/null | wc -l)
    if [ "$PROMPT_COUNT" -eq 0 ]; then
        print_warning "No prompt template files found in prompts/ directory"
        print_warning "Auto-suggestions will not be available"
    else
        print_success "Found $PROMPT_COUNT prompt template file(s)"
    fi
}

# Function to start the server
start_server() {
    print_status "Starting FastAPI server..."
    
    cd backend
    
    # Activate virtual environment
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        source venv/Scripts/activate
    else
        source venv/bin/activate
    fi
    
    # Start server in background
    print_status "Server starting on http://localhost:8000"
    print_status "Press Ctrl+C to stop the server"
    
    # Start uvicorn server
    uvicorn app:app --host 0.0.0.0 --port 8000 --reload
}

# Function to open browser
open_browser() {
    sleep 3  # Wait for server to start
    
    print_status "Opening application in default browser..."
    
    if command_exists xdg-open; then
        xdg-open http://localhost:8000 >/dev/null 2>&1 &
    elif command_exists open; then
        open http://localhost:8000 >/dev/null 2>&1 &
    elif command_exists start; then
        start http://localhost:8000 >/dev/null 2>&1 &
    else
        print_warning "Could not automatically open browser"
        print_status "Please manually open: http://localhost:8000"
    fi
}

# Function to display usage information
show_usage() {
    echo "AI Credit Aggregator - Deployment Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --help, -h          Show this help message"
    echo "  --no-browser        Don't automatically open browser"
    echo "  --port PORT         Specify custom port (default: 8000)"
    echo "  --host HOST         Specify custom host (default: 0.0.0.0)"
    echo ""
    echo "Examples:"
    echo "  $0                  # Standard deployment"
    echo "  $0 --no-browser     # Deploy without opening browser"
    echo "  $0 --port 3000      # Deploy on port 3000"
    echo ""
}

# Function to cleanup on exit
cleanup() {
    print_status "Cleaning up..."
    # Kill background processes if any
    jobs -p | xargs -r kill 2>/dev/null || true
}

# Set trap for cleanup
trap cleanup EXIT

# Main deployment function
main() {
    echo "=================================================="
    echo "🚀 AI Credit Aggregator - Deployment Script"
    echo "=================================================="
    echo ""
    
    # Parse command line arguments
    OPEN_BROWSER=true
    PORT=8000
    HOST="0.0.0.0"
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --help|-h)
                show_usage
                exit 0
                ;;
            --no-browser)
                OPEN_BROWSER=false
                shift
                ;;
            --port)
                PORT="$2"
                shift 2
                ;;
            --host)
                HOST="$2"
                shift 2
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # Deployment steps
    print_status "Starting deployment process..."
    echo ""
    
    # Step 1: Validate structure
    validate_structure
    
    # Step 2: Check Python
    check_python
    
    # Step 3: Setup virtual environment
    setup_venv
    
    # Step 4: Install dependencies
    install_dependencies
    
    # Step 5: Check sample data
    cd ..  # Go back to root directory
    check_sample_data
    
    echo ""
    print_success "✅ Deployment setup completed successfully!"
    echo ""
    
    # Display information
    echo "=================================================="
    echo "📋 Application Information"
    echo "=================================================="
    echo "🌐 URL: http://localhost:$PORT"
    echo "🔧 Admin Password: password"
    echo "📁 Models Directory: ./models/"
    echo "📝 Prompts Directory: ./prompts/"
    echo "🔄 Auto-refresh: Every 5 minutes"
    echo ""
    echo "=================================================="
    echo "🎯 Quick Start Guide"
    echo "=================================================="
    echo "1. Open http://localhost:$PORT in your browser"
    echo "2. View available AI models in the dashboard"
    echo "3. Enter prompts and get intelligent suggestions"
    echo "4. Use 'Admin' button with password 'password'"
    echo "5. Add new models and prompt templates"
    echo ""
    
    # Open browser if requested
    if [ "$OPEN_BROWSER" = true ]; then
        open_browser &
    fi
    
    # Start server (this will block)
    start_server
}

# Run main function
main "$@"
