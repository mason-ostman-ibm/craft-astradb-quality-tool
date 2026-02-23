#!/bin/bash

# AstraDB Quality Check Tool - Installation Script

set -e

echo "🚀 Installing AstraDB Quality Check Tool..."
echo ""

# Check Python version
echo "📋 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.9"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Error: Python 3.9 or higher is required. Found: $python_version"
    exit 1
fi
echo "✅ Python $python_version detected"
echo ""

# Create virtual environment
echo "📦 Creating virtual environment..."
if [ -d "venv" ]; then
    echo "⚠️  Virtual environment already exists. Skipping..."
else
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi
echo ""

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate
echo "✅ Virtual environment activated"
echo ""

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
echo "✅ pip upgraded"
echo ""

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt
echo "✅ Dependencies installed"
echo ""

# Install package in editable mode
echo "🔧 Installing astra-clean package..."
pip install -e .
echo "✅ Package installed"
echo ""

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Please edit .env file with your AstraDB credentials!"
    echo "   Required fields:"
    echo "   - ASTRA_DB_ENDPOINT"
    echo "   - ASTRA_DB_TOKEN"
    echo "   - ASTRA_DB_KEYSPACE"
    echo "   - ASTRA_DB_COLLECTION"
else
    echo "✅ .env file already exists"
fi
echo ""

# Create audit logs directory
echo "📁 Creating audit logs directory..."
mkdir -p audit_logs
echo "✅ Audit logs directory created"
echo ""

echo "🎉 Installation complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your AstraDB credentials"
echo "2. Activate the virtual environment: source venv/bin/activate"
echo "3. Test connection: astra-clean test-connection"
echo "4. View help: astra-clean --help"
echo ""
echo "For more information, see README.md or QUICK_START.md"
