#!/bin/bash

# Test GitHub Actions Workflows Locally
# This script helps test GitHub Actions workflows using the 'act' tool

set -e

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

# Check if act is installed
check_act() {
    if ! command -v act &> /dev/null; then
        print_error "act is not installed. Please install it first:"
        echo "  macOS: brew install act"
        echo "  Linux: curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash"
        echo "  Windows: choco install act-cli"
        exit 1
    fi
    print_success "act is installed"
}

# Check if Docker is running
check_docker() {
    if ! docker info &> /dev/null; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
    print_success "Docker is running"
}

# Test CI workflow
test_ci() {
    print_status "Testing CI workflow..."
    
    # Test with Python 3.11
    act push -W .github/workflows/ci.yml \
        --container-architecture linux/amd64 \
        --env-file .env.local \
        --secret-file .secrets.local \
        --matrix python-version:3.11 \
        --job test
    
    print_success "CI workflow test completed"
}

# Test Docker build workflow
test_docker_build() {
    print_status "Testing Docker build workflow..."
    
    act push -W .github/workflows/docker-build.yml \
        --container-architecture linux/amd64 \
        --env-file .env.local \
        --secret-file .secrets.local
    
    print_success "Docker build workflow test completed"
}

# Test release workflow
test_release() {
    print_status "Testing release workflow..."
    
    # Create a test release event
    act release -W .github/workflows/release.yml \
        --container-architecture linux/amd64 \
        --env-file .env.local \
        --secret-file .secrets.local
    
    print_success "Release workflow test completed"
}

# Test nightly workflow
test_nightly() {
    print_status "Testing nightly workflow..."
    
    act workflow_dispatch -W .github/workflows/nightly.yml \
        --container-architecture linux/amd64 \
        --env-file .env.local \
        --secret-file .secrets.local
    
    print_success "Nightly workflow test completed"
}

# Test all workflows
test_all() {
    print_status "Testing all workflows..."
    
    test_ci
    test_docker_build
    test_nightly
    
    print_success "All workflow tests completed"
}

# Show help
show_help() {
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  ci              Test CI workflow"
    echo "  docker          Test Docker build workflow"
    echo "  release         Test release workflow"
    echo "  nightly         Test nightly workflow"
    echo "  all             Test all workflows"
    echo "  help            Show this help message"
    echo ""
    echo "Prerequisites:"
    echo "  - act tool installed (https://github.com/nektos/act)"
    echo "  - Docker running"
    echo "  - .env.local file with environment variables (optional)"
    echo "  - .secrets.local file with secrets (optional)"
    echo ""
    echo "Examples:"
    echo "  $0 ci           # Test only CI workflow"
    echo "  $0 all          # Test all workflows"
}

# Create sample environment files if they don't exist
create_env_files() {
    if [ ! -f .env.local ]; then
        print_warning "Creating sample .env.local file"
        cat > .env.local << EOF
# Sample environment variables for local testing
# Modify these as needed for your environment
GITHUB_REPOSITORY=your-username/repomap-tool
GITHUB_REF=refs/heads/main
GITHUB_SHA=1234567890abcdef
EOF
    fi
    
    if [ ! -f .secrets.local ]; then
        print_warning "Creating sample .secrets.local file"
        cat > .secrets.local << EOF
# Sample secrets for local testing
# Add your actual secrets here for testing
GITHUB_TOKEN=your-github-token
CODECOV_TOKEN=your-codecov-token
EOF
    fi
}

# Main script logic
main() {
    print_status "Starting GitHub Actions workflow testing..."
    
    # Check prerequisites
    check_act
    check_docker
    
    # Create environment files if needed
    create_env_files
    
    # Parse command line arguments
    case "${1:-help}" in
        ci)
            test_ci
            ;;
        docker)
            test_docker_build
            ;;
        release)
            test_release
            ;;
        nightly)
            test_nightly
            ;;
        all)
            test_all
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
    
    print_success "Workflow testing completed successfully!"
}

# Run main function with all arguments
main "$@"
