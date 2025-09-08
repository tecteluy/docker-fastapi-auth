#!/bin/bash

# Test runner script for Docker Atrium Auth Service

set -e

echo "🧪 Running tests for Docker Atrium Auth Service"
echo "==============================================="

# Function to run tests
run_tests() {
    local test_type=$1
    local test_path=$2

    echo ""
    echo "📋 Running $test_type tests..."
    echo "-----------------------------------"

    if docker-compose --profile test ps | grep -q "test-runner"; then
        echo "Stopping existing test runner..."
        docker-compose --profile test stop test-runner
    fi

    # Run tests with coverage
    docker-compose --profile test run --rm test-runner pytest $test_path -v --tb=short --cov=app --cov-report=term-missing
}

# Check if test profile is requested
if [ "$1" = "--profile" ] && [ "$2" = "test" ]; then
    shift 2
fi

# Parse arguments
case "${1:-all}" in
    "unit")
        run_tests "Unit" "tests/unit/"
        ;;
    "integration")
        run_tests "Integration" "tests/integration/"
        ;;
    "e2e")
        run_tests "End-to-End" "tests/e2e/"
        ;;
    "all"|*)
        run_tests "All" "tests/"
        ;;
esac

echo ""
echo "✅ Test execution completed!"
