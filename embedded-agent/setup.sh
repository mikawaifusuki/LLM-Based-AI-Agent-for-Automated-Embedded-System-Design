#!/bin/bash

# Setup script for 8051 Embedded System Design Agent
echo "Setting up 8051 Embedded System Design Agent..."

# Create necessary directories
mkdir -p backend/outputs backend/kb/datasheets frontend/web-ui/build

# Create environment file if not exists
if [ ! -f .env ]; then
    echo "Creating .env file from example..."
    cp .env.example .env
    echo "Please update the .env file with your OpenAI API key."
fi

# Check if Python is installed
if command -v python3 &>/dev/null; then
    echo "Setting up Python environment..."
    
    # Create virtual environment if not exists
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        echo "Virtual environment created."
    fi
    
    # Activate virtual environment and install dependencies
    source venv/bin/activate
    pip install -r backend/requirements.txt
    
    echo "Python environment setup complete."
else
    echo "Python 3 not found. Please install Python 3 to continue."
    exit 1
fi

# Check if npm is installed
if command -v npm &>/dev/null; then
    echo "Setting up Node.js environment..."
    
    # Install frontend dependencies
    cd frontend/web-ui
    npm install
    cd ../..
    
    echo "Node.js environment setup complete."
else
    echo "npm not found. Frontend dependencies not installed."
    echo "Please install Node.js and npm to run the frontend."
fi

# Check if SDCC is installed
if command -v sdcc &>/dev/null; then
    echo "SDCC compiler found."
else
    echo "SDCC compiler not found. Please install SDCC for 8051 compilation."
    echo "Download from: http://sdcc.sourceforge.net/"
fi

# Check if Docker and Docker Compose are installed
if command -v docker &>/dev/null && command -v docker-compose &>/dev/null; then
    echo "Docker and Docker Compose found."
    echo "You can run the application using:"
    echo "docker-compose up -d"
else
    echo "Docker and/or Docker Compose not found."
    echo "You can run the backend and frontend manually:"
    echo "- Backend: cd backend && python -m uvicorn server:app --host 0.0.0.0 --port 8000"
    echo "- Frontend: cd frontend/web-ui && npm start"
fi

echo "Setup complete!"
echo "Remember to update your .env file with your OpenAI API key."
echo "To start the application:"
echo "1. With Docker: docker-compose up"
echo "2. Manually:"
echo "   - Backend: source venv/bin/activate && cd backend && uvicorn server:app --host 0.0.0.0 --port 8000"
echo "   - Frontend: cd frontend/web-ui && npm start" 