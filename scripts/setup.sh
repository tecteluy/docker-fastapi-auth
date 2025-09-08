#!/bin/bash

set -e

echo "🚀 Docker Atrium Auth Service - Quick Setup"
echo "==========================================="

# Check if we're in the right directory
if [ ! -f "LICENSE" ] || [ ! -f "README.md" ]; then
    echo "❌ Please run this script from the docker-atrium-auth root directory"
    exit 1
fi

echo "📋 Checking prerequisites..."

# Check if Docker is installed and running
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not available. Please install Docker Compose."
    exit 1
fi

echo "✅ Docker prerequisites met"

# Remove Lens migration logic; always setup from scratch
echo "⚠️  Skipping lens migration logic; setting up project from scratch."
MIGRATE_FROM_LENS=false

echo ""
echo "🔧 Setting up project structure..."

# Create basic structure if migration is not possible
if [ "$MIGRATE_FROM_LENS" = false ]; then
    echo "📁 Creating auth-service directory structure..."
    mkdir -p auth-service/{app/{models,services,routes,middleware},migrations,tests}
    
    # Create basic requirements.txt
    cat > auth-service/requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
alembic==1.12.1
psycopg2-binary==2.9.9
redis==5.0.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
httpx==0.25.2
pydantic==2.5.0
pydantic-settings==2.1.0
python-dotenv==1.0.0
EOF
    
    # Create basic Dockerfile
    cat > auth-service/Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
EOF

    echo "⚠️  Basic structure created. You'll need to implement the auth service code."
fi

# Create environment file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
    else
        cat > .env << 'EOF'
# OAuth Providers
GITHUB_CLIENT_ID=your_github_client_id_here
GITHUB_CLIENT_SECRET=your_github_client_secret_here
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here

# JWT Configuration
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-minimum-32-chars
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Database Configuration
POSTGRES_USER=atrium_auth
POSTGRES_PASSWORD=secure_password_change_this
POSTGRES_DB=atrium_auth
POSTGRES_PORT=5433

# Redis Configuration
REDIS_PASSWORD=secure_redis_password_change_this
REDIS_PORT=6380

# Application URLs
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8006

# Service Ports
AUTH_SERVICE_PORT=8006
AUTH_SERVICE_DEV_PORT=8007

# API Configuration
API_TOKEN=secure-api-token-change-this
EOF
    fi
    echo "⚠️  Please edit .env file with your actual configuration values"
fi

# Create docker-compose.yml if it doesn't exist
if [ ! -f "docker-compose.yml" ]; then
    echo "🐳 Creating Docker Compose configuration..."
    # The docker-compose.yml content will be created by the migration guide
    echo "⚠️  Please follow MIGRATION.md to create docker-compose.yml"
fi

echo ""
echo "✅ Basic setup completed!"
echo ""
echo "📖 Next Steps:"
echo "1. Read README.md for full documentation"
echo "2. Follow MIGRATION.md for detailed migration steps"

if [ "$MIGRATE_FROM_LENS" = true ]; then
    echo "3. Run: ./scripts/migrate_from_lens.sh"
else
    echo "3. Implement auth service code or copy from docker-atrium-lens"
fi

echo "4. Configure OAuth providers in .env file"
echo "5. Run: docker compose --profile dev up -d --build"
echo "6. Test: curl http://localhost:8006/health"
echo ""
echo "📚 Documentation:"
echo "   - README.md: Complete project documentation"
echo "   - MIGRATION.md: Detailed migration guide"
echo ""
echo "🆘 For help, check the troubleshooting section in MIGRATION.md"
