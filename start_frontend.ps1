# start_frontend.ps1
Write-Host "Starting frontend server..." -ForegroundColor Green

$frontendPath = "frontend/chip-quotation-frontend"
if (Test-Path $frontendPath) {
    Set-Location -Path $frontendPath
    
    # Check if package.json exists
    if (-not (Test-Path "package.json")) {
        Write-Host "ERROR: package.json not found!" -ForegroundColor Red
        exit 1
    }
    
    # Check if node_modules exists
    if (-not (Test-Path "node_modules")) {
        Write-Host "Installing dependencies..." -ForegroundColor Yellow
        npm install
    }
    
    # Check available scripts
    $packageJson = Get-Content "package.json" | ConvertFrom-Json
    $scripts = $packageJson.scripts
    
    Write-Host "Available scripts:" -ForegroundColor Cyan
    $scripts.PSObject.Properties | ForEach-Object {
        Write-Host "  npm run $($_.Name)" -ForegroundColor Cyan
    }
    
    # Try different script names in order of preference
    if ($scripts.dev) {
        Write-Host "Starting with 'dev' script..." -ForegroundColor Green
        Write-Host "Frontend will be available at http://localhost:3000" -ForegroundColor Cyan
        npm run dev
    } elseif ($scripts.start) {
        Write-Host "Starting with 'start' script..." -ForegroundColor Green
        Write-Host "Frontend will be available at http://localhost:3000" -ForegroundColor Cyan
        npm run start
    } else {
        Write-Host "ERROR: No suitable start script found!" -ForegroundColor Red
        Write-Host "Available scripts are listed above." -ForegroundColor Yellow
        Write-Host "Please add a 'dev' or 'start' script to package.json" -ForegroundColor Yellow
    }
} else {
    Write-Host "ERROR: Frontend directory not found at $frontendPath" -ForegroundColor Red
    Write-Host "Make sure the frontend code is in the correct location." -ForegroundColor Yellow
}