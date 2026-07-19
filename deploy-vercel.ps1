# Vercel Deployment Script
# This script will deploy the CleanLoop frontend to Vercel using the Vercel API

param(
    [string]$VercelToken,
    [string]$RailwayBackendUrl
)

Write-Host "Starting Vercel Frontend Deployment..." -ForegroundColor Green

# Set Vercel API endpoint
$vercelApiUrl = "https://api.vercel.com"

# Headers for Vercel API
$headers = @{
    "Authorization" = "Bearer $VercelToken"
    "Content-Type" = "application/json"
}

# Step 1: Create Project
Write-Host "Creating Vercel project..." -ForegroundColor Yellow
$projectPayload = @{
    name = "cleanloop"
    gitRepository = @{
        type = "github"
        repo = "tatasuresh/SwachhSanatan"
    }
} | ConvertTo-Json

$projectResponse = Invoke-RestMethod -Uri "$vercelApiUrl/v10/projects" -Method Post -Headers $headers -Body $projectPayload
$projectId = $projectResponse.id
Write-Host "Project created: $projectId" -ForegroundColor Green

# Step 2: Set Environment Variables
Write-Host "Setting environment variables..." -ForegroundColor Yellow
$envPayload = @{
    key = "VITE_API_URL"
    value = "$RailwayBackendUrl/api"
    target = @("production", "preview", "development")
} | ConvertTo-Json

Invoke-RestMethod -Uri "$vercelApiUrl/v10/projects/$projectId/env" -Method Post -Headers $headers -Body $envPayload | Out-Null
Write-Host "Environment variables configured" -ForegroundColor Green

# Step 3: Configure Build Settings
Write-Host "Configuring build settings..." -ForegroundColor Yellow
$buildPayload = @{
    rootDirectory = "frontend"
    buildCommand = "npm run build"
    outputDirectory = "dist"
} | ConvertTo-Json

Invoke-RestMethod -Uri "$vercelApiUrl/v10/projects/$projectId" -Method PATCH -Headers $headers -Body $buildPayload | Out-Null
Write-Host "Build settings configured" -ForegroundColor Green

# Step 4: Trigger Deployment
Write-Host "Triggering deployment..." -ForegroundColor Yellow
$deployPayload = @{
    gitMetadata = @{
        ref = "main"
    }
} | ConvertTo-Json

$deployResponse = Invoke-RestMethod -Uri "$vercelApiUrl/v13/deployments" -Method Post -Headers $headers -Body $deployPayload
$deploymentId = $deployResponse.id
Write-Host "Deployment triggered: $deploymentId" -ForegroundColor Green

Write-Host "Vercel deployment setup complete!" -ForegroundColor Green
Write-Host "Project ID: $projectId" -ForegroundColor Cyan
Write-Host "Deployment ID: $deploymentId" -ForegroundColor Cyan
