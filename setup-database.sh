#!/bin/bash
# Setup script for macOS - Automates PostgreSQL database creation

set -e

echo "🗄️  Setting up PostgreSQL Database"
echo "=================================="
echo ""

# Detect macOS architecture
if [[ $(uname -m) == "arm64" ]]; then
    PG_BIN="/opt/homebrew/opt/postgresql@15/bin"
    echo "✓ Detected Apple Silicon (M1/M2/M3)"
elif [[ $(uname -m) == "x86_64" ]]; then
    PG_BIN="/usr/local/opt/postgresql@15/bin"
    echo "✓ Detected Intel Mac"
else
    PG_BIN=""
    echo "⚠️  Unknown architecture"
fi

# Check if PostgreSQL is installed
if [ -d "$PG_BIN" ] && [ -f "$PG_BIN/psql" ]; then
    echo "✓ Found PostgreSQL at: $PG_BIN"
    export PATH="$PG_BIN:$PATH"
elif command -v psql &> /dev/null; then
    echo "✓ Found PostgreSQL in PATH"
    PG_BIN=$(dirname $(which psql))
else
    echo "❌ PostgreSQL not found!"
    echo ""
    echo "Please install PostgreSQL first:"
    echo "  brew install postgresql@15"
    echo "  brew services start postgresql@15"
    echo ""
    echo "Or use the manual setup in README.md"
    exit 1
fi

# Check if PostgreSQL service is running
if ! pg_isready &> /dev/null; then
    echo "⚠️  PostgreSQL service is not running"
    echo "Starting PostgreSQL service..."
    if [[ $(uname -m) == "arm64" ]]; then
        brew services start postgresql@15
    else
        brew services start postgresql@15
    fi
    sleep 3
fi

# Create user if it doesn't exist
echo ""
echo "Creating PostgreSQL user 'app'..."
if psql postgres -tAc "SELECT 1 FROM pg_roles WHERE rolname='app'" | grep -q 1; then
    echo "✓ User 'app' already exists"
else
    createuser -s app || psql postgres -c "CREATE USER app WITH PASSWORD 'app';"
    echo "✓ User 'app' created"
fi

# Create database if it doesn't exist
echo ""
echo "Creating database 'auditor'..."
if psql postgres -tAc "SELECT 1 FROM pg_database WHERE datname='auditor'" | grep -q 1; then
    echo "✓ Database 'auditor' already exists"
else
    createdb -O app auditor || psql postgres -c "CREATE DATABASE auditor OWNER app;"
    echo "✓ Database 'auditor' created"
fi

echo ""
echo "✅ Database setup complete!"
echo ""
echo "You can now continue with backend setup:"
echo "  cd backend"
echo "  python3 -m venv venv"
echo "  source venv/bin/activate"
echo "  pip install -r requirements.txt"
echo "  alembic upgrade head"
echo ""

