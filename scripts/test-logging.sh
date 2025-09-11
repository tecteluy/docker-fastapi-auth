#!/bin/bash

# Logging Test Runner Script
# Runs specific logging tests with appropriate configurations

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}FastAPI Auth Service - Logging Test Runner${NC}"
echo "=============================================="

# Function to run tests with specific markers
run_test_category() {
    local category=$1
    local description=$2
    
    echo -e "\n${YELLOW}Running $description...${NC}"
    echo "----------------------------------------"
    
    if pytest -m "$category" --tb=short -v; then
        echo -e "${GREEN}✅ $description passed${NC}"
    else
        echo -e "${RED}❌ $description failed${NC}"
        return 1
    fi
}

# Function to run specific test file
run_test_file() {
    local file_path=$1
    local description=$2
    
    echo -e "\n${YELLOW}Running $description...${NC}"
    echo "----------------------------------------"
    
    if pytest "$file_path" --tb=short -v; then
        echo -e "${GREEN}✅ $description passed${NC}"
    else
        echo -e "${RED}❌ $description failed${NC}"
        return 1
    fi
}

# Default: run all logging tests
if [ $# -eq 0 ]; then
    echo "Running all logging tests..."
    
    # Unit tests
    run_test_category "logging_unit" "Logging Unit Tests"
    
    # Integration tests
    run_test_category "logging_integration" "Logging Integration Tests" 
    
    # E2E tests
    run_test_category "logging_e2e" "Logging End-to-End Tests"
    
    echo -e "\n${GREEN}🎉 All logging tests completed!${NC}"
    
elif [ "$1" = "unit" ]; then
    run_test_file "tests/unit/test_logging_middleware.py" "Logging Middleware Unit Tests"
    
elif [ "$1" = "integration" ]; then
    run_test_file "tests/integration/test_logging_integration.py" "Logging Integration Tests"
    
elif [ "$1" = "e2e" ]; then
    run_test_file "tests/e2e/test_logging_e2e.py" "Logging End-to-End Tests"
    
elif [ "$1" = "performance" ]; then
    run_test_category "logging_performance" "Logging Performance Tests"
    
elif [ "$1" = "middleware" ]; then
    echo -e "\n${YELLOW}Running specific middleware tests...${NC}"
    pytest tests/unit/test_logging_middleware.py::TestRequestLoggingMiddleware --tb=short -v
    
elif [ "$1" = "masking" ]; then
    echo -e "\n${YELLOW}Running sensitive data masking tests...${NC}"
    pytest tests/unit/test_logging_middleware.py::TestRequestLoggingMiddleware::test_sensitive_data_masking* --tb=short -v
    
elif [ "$1" = "config" ]; then
    echo -e "\n${YELLOW}Running logging configuration tests...${NC}"
    pytest tests/unit/test_logging_middleware.py::TestLoggingConfiguration --tb=short -v
    
elif [ "$1" = "stress" ]; then
    echo -e "\n${YELLOW}Running logging stress tests...${NC}"
    pytest tests/e2e/test_logging_e2e.py::TestLoggingEndToEnd::test_high_load_logging --tb=short -v
    pytest tests/e2e/test_logging_e2e.py::TestLoggingEndToEnd::test_logging_during_service_stress --tb=short -v
    
elif [ "$1" = "help" ] || [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  (no args)     Run all logging tests"
    echo "  unit          Run only unit tests"
    echo "  integration   Run only integration tests" 
    echo "  e2e           Run only end-to-end tests"
    echo "  performance   Run only performance tests"
    echo "  middleware    Run middleware-specific tests"
    echo "  masking       Run sensitive data masking tests"
    echo "  config        Run configuration tests"
    echo "  stress        Run stress/load tests"
    echo "  help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                 # Run all logging tests"
    echo "  $0 unit           # Run unit tests only"
    echo "  $0 masking        # Test sensitive data masking"
    echo "  $0 stress         # Run stress tests"
    
else
    echo -e "${RED}❌ Unknown option: $1${NC}"
    echo "Use '$0 help' for usage information"
    exit 1
fi
