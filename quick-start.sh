#!/bin/bash

# Quick Start Script for Simple Hospital Information System
# This script will help you get the system up and running quickly

echo "=========================================="
echo "Simple Hospital Information System"
echo "Quick Start Installation"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version

if [ $? -ne 0 ]; then
    echo "❌ Python 3 is not installed. Please install Python 3.10 or higher."
    exit 1
fi

echo "✅ Python is installed"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "✅ Dependencies installed"
echo ""

# Check if database exists
if [ -f "hospital.db" ]; then
    echo "⚠️  Database already exists. Skipping initialization."
else
    echo "Creating initial admin user..."
    echo -e "admin\nمدیر سیستم\nadmin123" | python initial_admin.py
    
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create admin user"
        exit 1
    fi
    
    echo "✅ Admin user created"
fi

echo ""
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "Default Admin Credentials:"
echo "  Username: admin"
echo "  Password: admin123"
echo ""
echo "To start the server, run:"
echo "  python main.py"
echo ""
echo "Or:"
echo "  uvicorn main:app --reload"
echo ""
echo "Then open your browser to:"
echo "  http://localhost:8000"
echo ""
echo "=========================================="
echo "For more information, see README.md"
echo "=========================================="
