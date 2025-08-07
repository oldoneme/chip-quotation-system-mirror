# Navigate to backend directory
Set-Location -Path 'backend'

# Check if virtual environment exists
if (-not (Test-Path 'venv')) {
    Write-Host 'Creating virtual environment...' -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host 'Activating virtual environment...' -ForegroundColor Yellow
& venv/Scripts/Activate.ps1

# Install dependencies
Write-Host 'Installing dependencies...' -ForegroundColor Yellow
pip install -r requirements.txt

# Initialize database with sample data
Write-Host 'Initializing database...' -ForegroundColor Yellow
python init_data.py

# Start the backend server
Write-Host 'Starting backend server...' -ForegroundColor Yellow
Write-Host 'Backend API will be available at http://localhost:8000' -ForegroundColor Cyan
Write-Host 'API Documentation at http://localhost:8000/docs' -ForegroundColor Cyan
Write-Host 'Health check at http://localhost:8000/health' -ForegroundColor Cyan

# Run with specific host and port
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000