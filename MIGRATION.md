# Migration Guide: Auth Service from Lens to Standalone Project

This document provides step-by-step instructions for migrating the authentication service from `docker-atrium-lens` to the new standalone `docker-atrium-auth` project.

## Current State Analysis

### Source Location (docker-atrium-lens)
```
docker-atrium-lens/
├── auth-service/          # ← Source to migrate
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/
│   │   ├── services/
│   │   ├── routes/
│   │   └── middleware/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env
├── docker-compose.yml     # ← Extract auth services
└── .env.example          # ← Copy relevant config
```

### Target Structure (docker-atrium-auth)
```
docker-atrium-auth/
├── auth-service/          # ← Migrated code
├── docker-compose.yml     # ← Standalone compose
├── .env.example          # ← Auth-specific config
├── README.md             # ← This documentation
├── MIGRATION.md          # ← This file
└── scripts/              # ← Migration utilities
```

## Migration Steps

### Step 1: Copy Auth Service Code

```bash
# Navigate to auth project
cd /etc/docker/docker-atrium/docker-atrium-auth

# Copy entire auth service directory
cp -r ../docker-atrium-lens/auth-service/ ./

# Verify structure
ls -la auth-service/
```

### Step 2: Extract Docker Configuration

Create standalone `docker-compose.yml`:

```bash
# Create the docker-compose file
cat > docker-compose.yml << 'EOF'
services:
  # === Authentication Services ===
  
  # PostgreSQL database for auth service
  auth-db:
    profiles: ["dev", "prod", "test"]
    image: postgres:15
    container_name: atrium-auth-db
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-changeme}
      POSTGRES_DB: ${POSTGRES_DB:-atrium_auth}
      POSTGRES_HOST_AUTH_METHOD: ${POSTGRES_HOST_AUTH_METHOD:-scram-sha-256}
    volumes:
      - auth_postgres_data:/var/lib/postgresql/data
    ports:
      - "${POSTGRES_PORT:-5433}:5432"
    networks:
      - auth-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-postgres} -d ${POSTGRES_DB:-atrium_auth}"]
      interval: 30s
      timeout: 10s
      retries: 5

  # Redis for auth service sessions
  auth-redis:
    profiles: ["dev", "prod", "test"]
    image: redis:7-alpine
    container_name: atrium-auth-redis
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD:-}
    volumes:
      - auth_redis_data:/data
    ports:
      - "${REDIS_PORT:-6380}:6379"
    networks:
      - auth-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 5

  # Authentication service
  auth-service:
    profiles: ["dev", "prod"]
    build: 
      context: ./auth-service
      dockerfile: Dockerfile
    container_name: atrium-auth-service
    environment:
      # Database Configuration
      - POSTGRES_HOST=auth-db
      - POSTGRES_USER=${POSTGRES_USER:-postgres}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-changeme}
      - POSTGRES_DB=${POSTGRES_DB:-atrium_auth}
      - POSTGRES_PORT=5432
      
      # Redis Configuration
      - REDIS_URL=redis://:${REDIS_PASSWORD:-}@auth-redis:6379/0
      
      # OAuth Configuration
      - GITHUB_CLIENT_ID=${GITHUB_CLIENT_ID:-}
      - GITHUB_CLIENT_SECRET=${GITHUB_CLIENT_SECRET:-}
      - GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID:-}
      - GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET:-}
      
      # JWT Configuration
      - JWT_SECRET_KEY=${JWT_SECRET_KEY:-your-super-secret-jwt-key-change-this}
      - JWT_ALGORITHM=${JWT_ALGORITHM:-HS256}
      - JWT_ACCESS_TOKEN_EXPIRE_MINUTES=${JWT_ACCESS_TOKEN_EXPIRE_MINUTES:-30}
      - JWT_REFRESH_TOKEN_EXPIRE_DAYS=${JWT_REFRESH_TOKEN_EXPIRE_DAYS:-7}
      
      # Application URLs
      - FRONTEND_URL=${FRONTEND_URL:-http://localhost:3000}
      - BACKEND_URL=${BACKEND_URL:-http://localhost:8006}
      
      # API Configuration
      - API_TOKEN=${API_TOKEN:-changeme}
    depends_on:
      auth-db:
        condition: service_healthy
      auth-redis:
        condition: service_healthy
    ports:
      - "${AUTH_SERVICE_PORT:-8006}:8001"
    networks:
      - auth-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 30s

  # Development service with volume mounts
  auth-service-dev:
    profiles: ["dev"]
    build: 
      context: ./auth-service
      dockerfile: Dockerfile
    container_name: atrium-auth-service-dev
    environment:
      # Same as auth-service
      - POSTGRES_HOST=auth-db
      - POSTGRES_USER=${POSTGRES_USER:-postgres}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-changeme}
      - POSTGRES_DB=${POSTGRES_DB:-atrium_auth}
      - POSTGRES_PORT=5432
      - REDIS_URL=redis://:${REDIS_PASSWORD:-}@auth-redis:6379/0
      - GITHUB_CLIENT_ID=${GITHUB_CLIENT_ID:-}
      - GITHUB_CLIENT_SECRET=${GITHUB_CLIENT_SECRET:-}
      - GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID:-}
      - GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET:-}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY:-your-super-secret-jwt-key-change-this}
      - JWT_ALGORITHM=${JWT_ALGORITHM:-HS256}
      - JWT_ACCESS_TOKEN_EXPIRE_MINUTES=${JWT_ACCESS_TOKEN_EXPIRE_MINUTES:-30}
      - JWT_REFRESH_TOKEN_EXPIRE_DAYS=${JWT_REFRESH_TOKEN_EXPIRE_DAYS:-7}
      - FRONTEND_URL=${FRONTEND_URL:-http://localhost:3000}
      - BACKEND_URL=${BACKEND_URL:-http://localhost:8006}
      - API_TOKEN=${API_TOKEN:-changeme}
    volumes:
      - ./auth-service:/app
    depends_on:
      auth-db:
        condition: service_healthy
      auth-redis:
        condition: service_healthy
    ports:
      - "${AUTH_SERVICE_DEV_PORT:-8007}:8001"
    networks:
      - auth-network
    command: uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

  # Test runner
  test-runner:
    profiles: ["test"]
    build:
      context: ./auth-service
      dockerfile: Dockerfile
    container_name: atrium-auth-test-runner
    environment:
      - POSTGRES_HOST=auth-db
      - POSTGRES_USER=${POSTGRES_USER:-postgres}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-changeme}
      - POSTGRES_DB=atrium_auth_test
      - POSTGRES_PORT=5432
      - REDIS_URL=redis://:${REDIS_PASSWORD:-}@auth-redis:6379/1
      - JWT_SECRET_KEY=test-secret-key-for-testing-only
      - JWT_ALGORITHM=HS256
      - JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
      - JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
    volumes:
      - ./auth-service:/app
    depends_on:
      auth-db:
        condition: service_healthy
      auth-redis:
        condition: service_healthy
    networks:
      - auth-network
    command: pytest tests/ -v --tb=short

volumes:
  auth_postgres_data:
    name: atrium_auth_postgres_data
  auth_redis_data:
    name: atrium_auth_redis_data

networks:
  auth-network:
    name: atrium-auth-network
    driver: bridge
    external: false
EOF
```

### Step 3: Create Environment Configuration

```bash
# Copy and modify environment configuration
cp ../docker-atrium-lens/.env.example ./.env.example

# Create auth-specific .env.example
cat > .env.example << 'EOF'
# =============================================================================
# Docker Atrium Auth Service Configuration
# =============================================================================

# OAuth Providers Configuration
# -----------------------------------------------------------------------------
# GitHub OAuth Application (https://github.com/settings/developers)
GITHUB_CLIENT_ID=your_github_client_id_here
GITHUB_CLIENT_SECRET=your_github_client_secret_here

# Google OAuth Application (https://console.cloud.google.com/)
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here

# JWT Configuration
# -----------------------------------------------------------------------------
# Use a strong, random secret key (minimum 32 characters)
# Generate with: openssl rand -hex 32
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-minimum-32-chars
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Database Configuration
# -----------------------------------------------------------------------------
POSTGRES_USER=atrium_auth
POSTGRES_PASSWORD=secure_password_change_this
POSTGRES_DB=atrium_auth
POSTGRES_PORT=5433
POSTGRES_HOST_AUTH_METHOD=scram-sha-256

# Redis Configuration
# -----------------------------------------------------------------------------
REDIS_PASSWORD=secure_redis_password_change_this
REDIS_PORT=6380

# Application URLs
# -----------------------------------------------------------------------------
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8006

# Service Ports
# -----------------------------------------------------------------------------
AUTH_SERVICE_PORT=8006
AUTH_SERVICE_DEV_PORT=8007

# API Configuration
# -----------------------------------------------------------------------------
API_TOKEN=secure-api-token-change-this

# Development/Testing
# -----------------------------------------------------------------------------
# Set to development for verbose logging
ENVIRONMENT=production
DEBUG=false
EOF

# Create .env.template for deployment automation
cp .env.example .env.template
```

### Step 4: Create Migration Scripts

```bash
# Create scripts directory
mkdir -p scripts

# Create migration utility script
cat > scripts/migrate_from_lens.sh << 'EOF'
#!/bin/bash

set -e

echo "🚀 Migrating Auth Service from docker-atrium-lens..."

# Check if lens project exists
LENS_PATH="../docker-atrium-lens"
if [ ! -d "$LENS_PATH" ]; then
    echo "❌ docker-atrium-lens not found at $LENS_PATH"
    exit 1
fi

echo "📂 Copying auth service code..."
if [ -d "auth-service" ]; then
    echo "⚠️  auth-service directory already exists. Backing up..."
    mv auth-service auth-service.backup.$(date +%Y%m%d_%H%M%S)
fi

cp -r "$LENS_PATH/auth-service" ./
echo "✅ Auth service code copied"

echo "📝 Updating configuration files..."
# Update any lens-specific configurations
if [ -f "auth-service/app/config.py" ]; then
    # Update default ports and URLs if needed
    sed -i 's/localhost:8006/localhost:8006/g' auth-service/app/config.py
fi

echo "📦 Installing dependencies..."
cd auth-service
if [ -f "requirements.txt" ]; then
    echo "Dependencies found in requirements.txt"
else
    echo "❌ requirements.txt not found in auth-service"
    exit 1
fi
cd ..

echo "🔧 Setting up environment..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "⚠️  Please edit .env file with your OAuth credentials"
fi

echo "🐳 Building Docker images..."
docker compose build

echo "✅ Migration completed successfully!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your OAuth provider credentials"
echo "2. Run: docker compose --profile dev up -d"
echo "3. Test: curl http://localhost:8006/health"
echo "4. Update docker-atrium-lens to use external auth service"
EOF

chmod +x scripts/migrate_from_lens.sh

# Create database migration script
cat > scripts/setup_database.sh << 'EOF'
#!/bin/bash

set -e

echo "🗄️  Setting up auth service database..."

# Start database services
echo "📦 Starting database services..."
docker compose up auth-db auth-redis -d

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
timeout 60 bash -c 'until docker compose exec auth-db pg_isready -U ${POSTGRES_USER:-postgres} -d ${POSTGRES_DB:-atrium_auth}; do sleep 2; done'

# Run database migrations
echo "🔄 Running database migrations..."
docker compose exec auth-service alembic upgrade head

echo "✅ Database setup completed!"
EOF

chmod +x scripts/setup_database.sh

# Create test script
cat > scripts/run_tests.sh << 'EOF'
#!/bin/bash

set -e

echo "🧪 Running auth service tests..."

# Start test environment
docker compose --profile test up test-runner

# Check test results
if [ $? -eq 0 ]; then
    echo "✅ All tests passed!"
else
    echo "❌ Tests failed!"
    exit 1
fi
EOF

chmod +x scripts/run_tests.sh
```

### Step 5: Update Lens Project Configuration

Create instructions for updating the lens project:

```bash
cat > LENS_INTEGRATION.md << 'EOF'
# Integrating External Auth Service with docker-atrium-lens

## Updates Required in docker-atrium-lens

### 1. Update docker-compose.yml

Remove auth services from lens docker-compose.yml and add external network:

```yaml
# Remove these services:
# - auth-db
# - auth-redis  
# - auth-service

# Update lens service environment
services:
  lens:
    environment:
      NEXT_PUBLIC_AUTH_API_URL: http://localhost:8006  # External auth service
      # ... other env vars

  lens-dev:
    environment:
      NEXT_PUBLIC_AUTH_API_URL: http://localhost:8006  # External auth service
      # ... other env vars

# Add external network
networks:
  atrium-network:
    external: true
    name: atrium-auth-network
```

### 2. Update Frontend Configuration

Update auth API client in frontend:

```javascript
// frontend/utils/apiClient.js
const AUTH_API_URL = process.env.NEXT_PUBLIC_AUTH_API_URL || 'http://localhost:8006';

export const authApiClient = {
  baseURL: AUTH_API_URL,
  // ... existing auth client code
};
```

### 3. Start Services in Correct Order

```bash
# 1. Start auth service first
cd docker-atrium-auth
docker compose --profile prod up -d

# 2. Start lens service
cd ../docker-atrium-lens
docker compose --profile prod up -d
```

### 4. Environment Variables

Update lens .env file:
```bash
# Remove auth service related variables
# Add external auth service URL
NEXT_PUBLIC_AUTH_API_URL=http://localhost:8006
```
EOF
```

### Step 6: Execute Migration

```bash
# Run the migration script
./scripts/migrate_from_lens.sh

# Setup environment
cp .env.example .env
echo "Please edit .env with your OAuth credentials before proceeding"
```

### Step 7: Verification Steps

```bash
# Test the migration
cat > scripts/verify_migration.sh << 'EOF'
#!/bin/bash

set -e

echo "🔍 Verifying auth service migration..."

# Check if all files exist
FILES=(
    "auth-service/app/main.py"
    "auth-service/Dockerfile" 
    "auth-service/requirements.txt"
    "docker-compose.yml"
    ".env.example"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file exists"
    else
        echo "❌ $file missing"
        exit 1
    fi
done

# Check if services can start
echo "🐳 Testing Docker services..."
docker compose config > /dev/null
echo "✅ Docker compose configuration valid"

# Test build
echo "🔨 Testing build..."
docker compose build auth-service > /dev/null
echo "✅ Auth service builds successfully"

echo "✅ Migration verification completed!"
EOF

chmod +x scripts/verify_migration.sh

# Run verification
./scripts/verify_migration.sh
```

## Post-Migration Tasks

1. **Configure OAuth Providers**:
   - Setup GitHub OAuth app
   - Setup Google OAuth app
   - Update `.env` with credentials

2. **Test Standalone Service**:
```bash
docker compose --profile dev up -d
curl http://localhost:8006/health
```

3. **Update Dependent Services**:
   - Modify `docker-atrium-lens` to use external auth
   - Update `docker-atrium-nexus` for JWT authentication
   - Configure other Atrium services

4. **Setup Monitoring**:
   - Add health checks
   - Configure logging
   - Setup alerts

## Rollback Plan

If issues occur, you can rollback:

```bash
# Stop new auth service
cd docker-atrium-auth
docker compose down

# Restore lens with embedded auth
cd ../docker-atrium-lens
git checkout HEAD -- docker-compose.yml
docker compose up -d
```

## Next Steps

1. Complete OAuth provider setup
2. Test authentication flows
3. Update lens project integration
4. Extend to other Atrium services
5. Setup production deployment

## Troubleshooting

### Common Issues

1. **Database Connection Issues**:
```bash
# Check database status
docker compose logs auth-db
docker compose exec auth-db pg_isready -U postgres
```

2. **Port Conflicts**:
```bash
# Check if ports are in use
netstat -tulpn | grep :8006
lsof -i :8006
```

3. **OAuth Configuration**:
```bash
# Verify environment variables
docker compose exec auth-service env | grep -E "(GITHUB|GOOGLE)"
```

4. **Network Issues**:
```bash
# Check network connectivity
docker compose exec auth-service ping auth-db
docker compose exec auth-service ping auth-redis
```
EOF
