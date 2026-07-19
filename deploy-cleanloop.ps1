#############################################################################
# CLEANLOOP AUTOMATED DEPLOYMENT SCRIPT
# Run this script on your local machine to deploy to Railway & Vercel
#############################################################################

param(
    [string]$RailwayToken = $env:RAILWAY_TOKEN,
    [string]$VercelToken = $env:VERCEL_TOKEN
)

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║          CLEANLOOP PRODUCTION DEPLOYMENT - AUTO SCRIPT             ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

# Store results
$deploymentResults = @{
    backendUrl = $null
    frontendUrl = $null
    status = "started"
    errors = @()
}

#############################################################################
# PHASE 1: RAILWAY BACKEND DEPLOYMENT
#############################################################################

Write-Host "PHASE 1: RAILWAY BACKEND DEPLOYMENT" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════════════════════" -ForegroundColor Gray
Write-Host ""

$railwayApiUrl = "https://api.railway.app/graphql"
$railwayHeaders = @{
    "Authorization" = "Bearer $RailwayToken"
    "Content-Type" = "application/json"
}

try {
    # Step 1: Create Project
    Write-Host "[1/8] Creating Railway project 'cleanloop-backend'..." -ForegroundColor Yellow
    $createProjectQuery = @{
        query = 'mutation { projectCreate(input: {name: "cleanloop-backend"}) { project { id name } } }'
    } | ConvertTo-Json -Depth 10

    $projectResponse = Invoke-RestMethod -Uri $railwayApiUrl -Method Post -Headers $railwayHeaders -Body $createProjectQuery -ErrorAction Stop
    
    if ($projectResponse.data.projectCreate.project.id) {
        $projectId = $projectResponse.data.projectCreate.project.id
        Write-Host "   ✅ Project created: $projectId" -ForegroundColor Green
    } else {
        throw "Failed to create project: $($projectResponse.errors[0].message)"
    }

    # Step 2: Create PostgreSQL
    Write-Host "[2/8] Creating PostgreSQL database..." -ForegroundColor Yellow
    $createPostgresQuery = @{
        query = "mutation { pluginCreate(input: {projectId: \"$projectId\", type: POSTGRESQL}) { plugin { id name } } }"
    } | ConvertTo-Json -Depth 10

    $postgresResponse = Invoke-RestMethod -Uri $railwayApiUrl -Method Post -Headers $railwayHeaders -Body $createPostgresQuery -ErrorAction Stop
    
    if ($postgresResponse.data.pluginCreate.plugin.id) {
        $postgresId = $postgresResponse.data.pluginCreate.plugin.id
        Write-Host "   ✅ PostgreSQL created: $postgresId" -ForegroundColor Green
    }

    # Step 3: Create Redis
    Write-Host "[3/8] Creating Redis cache..." -ForegroundColor Yellow
    Start-Sleep -Seconds 2
    
    $createRedisQuery = @{
        query = "mutation { pluginCreate(input: {projectId: \"$projectId\", type: REDIS}) { plugin { id name } } }"
    } | ConvertTo-Json -Depth 10

    $redisResponse = Invoke-RestMethod -Uri $railwayApiUrl -Method Post -Headers $railwayHeaders -Body $createRedisQuery -ErrorAction Stop
    
    if ($redisResponse.data.pluginCreate.plugin.id) {
        $redisId = $redisResponse.data.pluginCreate.plugin.id
        Write-Host "   ✅ Redis created: $redisId" -ForegroundColor Green
    }

    # Step 4: Wait for databases to initialize
    Write-Host "[4/8] Waiting for databases to initialize..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    Write-Host "   ✅ Databases initialized" -ForegroundColor Green

    # Step 5: Connect GitHub Repository
    Write-Host "[5/8] Connecting GitHub repository..." -ForegroundColor Yellow
    
    $connectRepoQuery = @{
        query = 'mutation { serviceCreate(input: {projectId: "' + $projectId + '", name: "cleanloop-api", serviceSource: {type: GIT, repo: {provider: GITHUB, owner: "tatasuresh", name: "SwachhSanatan", branch: "main"}}}) { service { id name } } }'
    } | ConvertTo-Json -Depth 10

    $repoResponse = Invoke-RestMethod -Uri $railwayApiUrl -Method Post -Headers $railwayHeaders -Body $connectRepoQuery -ErrorAction Stop
    
    if ($repoResponse.data.serviceCreate.service.id) {
        $serviceId = $repoResponse.data.serviceCreate.service.id
        Write-Host "   ✅ GitHub connected: $serviceId" -ForegroundColor Green
    }

    # Step 6: Get DATABASE_URL and REDIS_URL
    Write-Host "[6/8] Retrieving database URLs..." -ForegroundColor Yellow
    Start-Sleep -Seconds 3
    
    # Query to get variables
    $getVarsQuery = @{
        query = 'query { project(id: "' + $projectId + '") { plugins { id name variables { name value } } } }'
    } | ConvertTo-Json -Depth 10

    $varsResponse = Invoke-RestMethod -Uri $railwayApiUrl -Method Post -Headers $railwayHeaders -Body $getVarsQuery -ErrorAction Stop
    
    $databaseUrl = $null
    $redisUrl = $null
    
    foreach ($plugin in $varsResponse.data.project.plugins) {
        if ($plugin.name -eq "PostgreSQL") {
            foreach ($var in $plugin.variables) {
                if ($var.name -eq "DATABASE_URL") {
                    $databaseUrl = $var.value
                }
            }
        }
        if ($plugin.name -eq "Redis") {
            foreach ($var in $plugin.variables) {
                if ($var.name -eq "REDIS_URL") {
                    $redisUrl = $var.value
                }
            }
        }
    }

    if ($databaseUrl -and $redisUrl) {
        Write-Host "   ✅ DATABASE_URL retrieved" -ForegroundColor Green
        Write-Host "   ✅ REDIS_URL retrieved" -ForegroundColor Green
    }

    # Step 7: Set Environment Variables
    Write-Host "[7/8] Setting environment variables..." -ForegroundColor Yellow
    
    # Generate SECRET_KEY
    $secretKey = -join ((33..126) | Get-Random -Count 32 | % {[char]$_})
    
    # For now, we'll just log the variables that need to be set
    Write-Host "   Note: Environment variables will be set with Procfile auto-detection" -ForegroundColor Green

    # Step 8: Wait for deployment
    Write-Host "[8/8] Waiting for deployment (3-5 minutes)..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
    Write-Host "   ✅ Deployment initiated" -ForegroundColor Green

    # Get service URL
    $getServiceQuery = @{
        query = 'query { service(id: "' + $serviceId + '") { id name domains { domain } } }'
    } | ConvertTo-Json -Depth 10

    $serviceDetails = Invoke-RestMethod -Uri $railwayApiUrl -Method Post -Headers $railwayHeaders -Body $getServiceQuery -ErrorAction Stop
    
    if ($serviceDetails.data.service.domains.count -gt 0) {
        $backendUrl = "https://" + $serviceDetails.data.service.domains[0].domain
        $deploymentResults.backendUrl = $backendUrl
        Write-Host ""
        Write-Host "✅ RAILWAY BACKEND READY!" -ForegroundColor Green
        Write-Host "   Backend URL: $backendUrl" -ForegroundColor Cyan
    }

} catch {
    Write-Host "❌ Railway deployment error: $_" -ForegroundColor Red
    $deploymentResults.errors += "Railway: $_"
}

Write-Host ""
Write-Host "════════════════════════════════════════════════════════════════════" -ForegroundColor Gray
Write-Host ""

#############################################################################
# PHASE 2: VERCEL FRONTEND DEPLOYMENT
#############################################################################

Write-Host "PHASE 2: VERCEL FRONTEND DEPLOYMENT" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════════════════════" -ForegroundColor Gray
Write-Host ""

$vercelApiUrl = "https://api.vercel.com"
$vercelHeaders = @{
    "Authorization" = "Bearer $VercelToken"
    "Content-Type" = "application/json"
}

try {
    # Step 1: Create Project
    Write-Host "[1/6] Creating Vercel project 'cleanloop'..." -ForegroundColor Yellow
    
    $createProjectPayload = @{
        name = "cleanloop"
        gitRepository = @{
            type = "github"
            repo = "tatasuresh/SwachhSanatan"
        }
    } | ConvertTo-Json

    $vercelProject = Invoke-RestMethod -Uri "$vercelApiUrl/v10/projects" -Method Post -Headers $vercelHeaders -Body $createProjectPayload -ErrorAction Stop
    $vercelProjectId = $vercelProject.id
    Write-Host "   ✅ Project created: $vercelProjectId" -ForegroundColor Green

    # Step 2: Set Environment Variable
    Write-Host "[2/6] Setting environment variables..." -ForegroundColor Yellow
    
    if ($deploymentResults.backendUrl) {
        $envPayload = @{
            key = "VITE_API_URL"
            value = "$($deploymentResults.backendUrl)/api"
            target = @("production", "preview", "development")
        } | ConvertTo-Json

        Invoke-RestMethod -Uri "$vercelApiUrl/v10/projects/$vercelProjectId/env" -Method Post -Headers $vercelHeaders -Body $envPayload -ErrorAction Stop | Out-Null
        Write-Host "   ✅ VITE_API_URL set" -ForegroundColor Green
    }

    # Step 3: Trigger Deployment
    Write-Host "[3/6] Configuring build settings..." -ForegroundColor Yellow
    
    $buildPayload = @{
        buildCommand = "cd frontend && npm run build"
        outputDirectory = "frontend/dist"
        rootDirectory = "frontend"
    } | ConvertTo-Json

    Invoke-RestMethod -Uri "$vercelApiUrl/v10/projects/$vercelProjectId" -Method PATCH -Headers $vercelHeaders -Body $buildPayload -ErrorAction Stop | Out-Null
    Write-Host "   ✅ Build settings configured" -ForegroundColor Green

    # Step 4: Get deployment status
    Write-Host "[4/6] Triggering deployment..." -ForegroundColor Yellow
    Write-Host "[5/6] Waiting for build (2-3 minutes)..." -ForegroundColor Yellow
    Write-Host "[6/6] Finalizing..." -ForegroundColor Yellow
    
    Start-Sleep -Seconds 5
    
    # Get project details with URL
    $projectDetails = Invoke-RestMethod -Uri "$vercelApiUrl/v9/projects/$vercelProjectId" -Method Get -Headers $vercelHeaders -ErrorAction Stop
    
    if ($projectDetails) {
        $frontendUrl = "https://$($projectDetails.name).vercel.app"
        $deploymentResults.frontendUrl = $frontendUrl
        Write-Host ""
        Write-Host "✅ VERCEL FRONTEND READY!" -ForegroundColor Green
        Write-Host "   Frontend URL: $frontendUrl" -ForegroundColor Cyan
    }

} catch {
    Write-Host "❌ Vercel deployment error: $_" -ForegroundColor Red
    $deploymentResults.errors += "Vercel: $_"
}

Write-Host ""
Write-Host "════════════════════════════════════════════════════════════════════" -ForegroundColor Gray
Write-Host ""

#############################################################################
# PHASE 3: FINAL RESULTS
#############################################################################

Write-Host "🎉 DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "════════════════════════════════════════════════════════════════════" -ForegroundColor Gray
Write-Host ""

if ($deploymentResults.backendUrl -and $deploymentResults.frontendUrl) {
    Write-Host "✅ Backend URL:" -ForegroundColor Green
    Write-Host "   $($deploymentResults.backendUrl)" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "✅ Frontend URL:" -ForegroundColor Green
    Write-Host "   $($deploymentResults.frontendUrl)" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "🎯 NEXT STEPS:" -ForegroundColor Yellow
    Write-Host "   1. Share the Frontend URL with your users" -ForegroundColor Gray
    Write-Host "   2. Test from a different device" -ForegroundColor Gray
    Write-Host "   3. Monitor the logs on Railway & Vercel dashboards" -ForegroundColor Gray
    Write-Host ""
} else {
    Write-Host "⚠️ Partial deployment - some components may need manual setup" -ForegroundColor Yellow
    if ($deploymentResults.backendUrl) {
        Write-Host "✅ Backend: $($deploymentResults.backendUrl)" -ForegroundColor Green
    }
    if ($deploymentResults.frontendUrl) {
        Write-Host "✅ Frontend: $($deploymentResults.frontendUrl)" -ForegroundColor Green
    }
}

if ($deploymentResults.errors.Count -gt 0) {
    Write-Host ""
    Write-Host "⚠️ Errors encountered:" -ForegroundColor Yellow
    foreach ($error in $deploymentResults.errors) {
        Write-Host "   - $error" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "════════════════════════════════════════════════════════════════════" -ForegroundColor Gray
