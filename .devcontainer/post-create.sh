#!/bin/bash
set -e

echo "Setting up Gemini CLI development environment..."

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

# Set up Python virtual environment with uv
print_status "Setting up Python virtual environment with uv..."
if [ ! -d ".venv" ]; then
    uv venv
    print_success "Created Python virtual environment with uv"
else
    print_success "Python virtual environment already exists"
fi

# Install dependencies with uv
print_status "Installing Python dependencies with uv..."
uv sync
print_success "Dependencies installed with uv"

# Activate virtual environment
source .venv/bin/activate
print_success "Virtual environment activated"

# Start Celery worker in the background
print_status "Starting Redis server..."
sudo service redis-server start
print_success "Redis server started."

print_status "Starting Celery worker..."
sudo celery -A app.tasks worker --loglevel=info &> celery_worker.log &
print_success "Celery worker started in the background."

# Install dependencies (only if package.json exists)
if [ -f "package.json" ]; then
    print_status "Installing npm dependencies..."
    if npm ci --no-audit --prefer-offline; then
        print_success "Dependencies installed successfully"
    else
        print_error "Failed to install dependencies"
        exit 1
    fi

    # Generate git commit info and build
    print_status "Building the project..."
    if npm run build 2>/dev/null; then
        print_success "Project built successfully"
    else
        print_warning "Build failed, but continuing..."
    fi
else
    print_warning "No package.json found - skipping npm project operations"
fi

# Set up git configuration
print_status "Setting up Git configuration..."

# Check if host Git config exists and copy it
if [ -f /tmp/.gitconfig-host ]; then
    cp /tmp/.gitconfig-host ~/.gitconfig
    print_success "Copied Git configuration from host"
elif [ ! -f ~/.gitconfig ]; then
    print_warning "No Git configuration found"
fi

# Set up SSH if available
if [ -d /tmp/.ssh-host ]; then
    cp -r /tmp/.ssh-host ~/.ssh
    chmod 700 ~/.ssh
    chmod 600 ~/.ssh/* 2>/dev/null || true
    print_success "Copied SSH keys from host"
fi

# Create useful scripts
print_status "Creating development helpers..."

# .env.example template is now created during Docker build
if [ -f ".env.example" ]; then
    print_success ".env.example template available"
fi

# Display useful information
echo ""
echo "Development environment ready!"
echo ""

# Show Node.js specific information only if package.json exists
if [ -f "package.json" ]; then
    print_success "Available npm scripts:"
    echo "  npm run build          - Build the project"
    echo "  npm run start          - Start the CLI in development mode"
    echo "  npm run debug          - Start with debugging enabled"
    echo "  npm run test           - Run tests"
    echo "  npm run lint           - Run linting"
    echo "  npm run format         - Format code with Prettier"
    echo "  npm run preflight      - Run full preflight checks"
    echo ""
    print_success "Development workflow:"
    echo "  1. Set up your GEMINI_API_KEY environment variable"
    echo "  2. Activate Python venv: source .venv/bin/activate"
    echo "  3. Run 'npm run build' to build the project"
    echo "  4. Run 'npm start' to start the CLI"
    echo "  5. Or run 'npx @google/gemini-cli' to test the published version"
    echo ""
    print_success "VS Code is configured with:"
    echo "  âœ… TypeScript support"
    echo "  âœ… ESLint integration"
    echo "  âœ… Prettier formatting"
    echo "  âœ… Debug configuration"
    echo "  âœ… Git integration"
    echo "  âœ… Python virtual environment"
else
    print_success "Development workflow:"
    echo "  1. Set up your GEMINI_API_KEY environment variable"
    echo "  2. Activate Python venv: source .venv/bin/activate"
    echo "  3. Use 'gemini-cli' command to interact with Gemini API"
    echo "  4. Start coding in your preferred language"
    echo ""
    print_success "VS Code is configured with:"
    echo "  âœ… Python support"
    echo "  âœ… Git integration"
    echo "  âœ… Python virtual environment"
    echo "  âœ… Gemini CLI globally installed"
fi

print_success "Happy coding!"
