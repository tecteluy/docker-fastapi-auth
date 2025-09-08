#!/bin/bash

# =============================================================================
# Docker Atrium Auth Service - Backup User Management Script
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to generate SHA256 hash
generate_hash() {
    local password="$1"
    if [ -z "$password" ]; then
        echo -e "${RED}Error: Password cannot be empty${NC}"
        exit 1
    fi
    echo -n "$password" | sha256sum | cut -d' ' -f1
}

# Function to create backup user configuration
create_backup_user() {
    local username="$1"
    local password="$2"
    local is_admin="${3:-false}"
    local permissions="${4:-[]}"

    if [ -z "$username" ] || [ -z "$password" ]; then
        echo -e "${RED}Error: Username and password are required${NC}"
        echo "Usage: $0 create-user <username> <password> [is_admin] [permissions]"
        exit 1
    fi

    local password_hash=$(generate_hash "$password")

    echo -e "${BLUE}Creating backup user configuration:${NC}"
    echo "Username: $username"
    echo "Password Hash: $password_hash"
    echo "Is Admin: $is_admin"
    echo "Permissions: $permissions"
    echo

    # Generate JSON configuration
    local user_config=$(cat <<EOF
  "$username": {
    "password_hash": "$password_hash",
    "is_admin": $is_admin,
    "permissions": $permissions
  }
EOF
)

    echo -e "${GREEN}Add this to your .env file under BACKUP_USERS:${NC}"
    echo "$user_config"
}

# Function to show usage
show_usage() {
    echo -e "${BLUE}Docker Atrium Auth Service - Backup User Management${NC}"
    echo
    echo "Usage:"
    echo "  $0 hash <password>              - Generate SHA256 hash for password"
    echo "  $0 create-user <username> <password> [is_admin] [permissions]"
    echo "                                   - Create backup user configuration"
    echo "  $0 list-users                   - List all configured backup users"
    echo "  $0 example-config               - Show example BACKUP_USERS configuration"
    echo "  $0 help                         - Show this help message"
    echo
    echo "Examples:"
    echo "  $0 hash mypassword123"
    echo "  $0 create-user admin mypassword123 true '{\"services\": [\"*\"]}'"
    echo "  $0 create-user operator oppass123 false '{\"services\": [\"read\", \"write\"]}'"
    echo "  $0 list-users"
    echo
}

# Function to list backup users
list_backup_users() {
    local env_file="$PROJECT_ROOT/.env"
    
    if [ ! -f "$env_file" ]; then
        echo -e "${RED}Error: .env file not found at $env_file${NC}"
        exit 1
    fi
    
    echo -e "${BLUE}Current Backup Users Configuration:${NC}"
    echo "========================================"
    
    # Check for BACKUP_USERS (multiple users)
    if grep -q "^BACKUP_USERS=" "$env_file"; then
        echo -e "${GREEN}Multiple Users Configuration Found:${NC}"
        echo
        
        # Extract BACKUP_USERS value
        local backup_users=$(grep "^BACKUP_USERS=" "$env_file" | cut -d'=' -f2- | sed 's/^"//' | sed 's/"$//')
        
        if [ -n "$backup_users" ]; then
            # Parse JSON and extract usernames
            echo "$backup_users" | python3 -c "
import sys
import json
try:
    users = json.loads(sys.stdin.read())
    print(f'Found {len(users)} backup users:')
    print()
    for username, config in users.items():
        is_admin = 'Yes' if config.get('is_admin', False) else 'No'
        permissions = config.get('permissions', {})
        print(f'  Username: {username}')
        print(f'  Admin: {is_admin}')
        print(f'  Permissions: {permissions}')
        print()
except json.JSONDecodeError as e:
    print('Error parsing BACKUP_USERS JSON:', str(e))
except Exception as e:
    print('Error:', str(e))
"
        else
            echo -e "${YELLOW}BACKUP_USERS is empty${NC}"
        fi
    fi
    
    # Check for legacy single user configuration
    if grep -q "^BACKUP_ADMIN_USERNAME=" "$env_file"; then
        echo -e "${GREEN}Legacy Single User Configuration Found:${NC}"
        echo
        
        local username=$(grep "^BACKUP_ADMIN_USERNAME=" "$env_file" | cut -d'=' -f2)
        local has_password=$(grep -q "^BACKUP_ADMIN_PASSWORD_HASH=" "$env_file" && echo "Yes" || echo "No")
        
        echo "  Username: $username"
        echo "  Password Hash Configured: $has_password"
        echo "  Admin: Yes (legacy default)"
        echo "  Permissions: All services (legacy default)"
        echo
        echo -e "${YELLOW}Note: Consider migrating to BACKUP_USERS format for better security${NC}"
    fi
    
    if ! grep -q "^BACKUP_USERS=" "$env_file" && ! grep -q "^BACKUP_ADMIN_USERNAME=" "$env_file"; then
        echo -e "${YELLOW}No backup users configured${NC}"
        echo
        echo "To add backup users, use:"
        echo "  $0 create-user <username> <password> [is_admin] [permissions]"
        echo "  $0 example-config"
    fi
}

# Function to show example configuration
show_example_config() {
    echo -e "${BLUE}Example BACKUP_USERS configuration for .env file:${NC}"
    echo
    echo "# Multiple backup users configuration"
    echo "BACKUP_USERS={"
    echo "  \"admin\": {"
    echo "    \"password_hash\": \"$(generate_hash "admin123")\","    echo "    \"is_admin\": true,"
    echo "    \"permissions\": {\"services\": [\"*\"]}"
    echo "  },"
    echo "  \"operator\": {"
    echo "    \"password_hash\": \"$(generate_hash "operator123")\","    echo "    \"is_admin\": false,"
    echo "    \"permissions\": {\"services\": [\"read\", \"write\"]}"
    echo "  },"
    echo "  \"viewer\": {"
    echo "    \"password_hash\": \"$(generate_hash "viewer123")\","    echo "    \"is_admin\": false,"
    echo "    \"permissions\": {\"services\": [\"read\"]}"
    echo "  }"
    echo "}"
    echo
    echo -e "${YELLOW}Note: Replace the example passwords with secure ones!${NC}"
}

# Main script logic
case "${1:-help}" in
    "hash")
        if [ -z "$2" ]; then
            echo -e "${RED}Error: Password is required${NC}"
            echo "Usage: $0 hash <password>"
            exit 1
        fi
        password_hash=$(generate_hash "$2")
        echo -e "${GREEN}SHA256 Hash for '$2':${NC}"
        echo "$password_hash"
        ;;
    "create-user")
        create_backup_user "$2" "$3" "$4" "$5"
        ;;
    "list-users")
        list_backup_users
        ;;
    "example-config")
        show_example_config
        ;;
    "help"|*)
        show_usage
        ;;
esac
