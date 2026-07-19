# Railway Deployment Script
# This script will deploy the CleanLoop backend to Railway using the Railway API

param(
    [string]$RailwayToken,
    [string]$OpenAIKey,
    [string]$AwsAccessKey,
    [string]$AwsSecretKey,
    [string]$SmtpUser,
    [string]$SmtpPassword
)

Write-Host "Starting Railway Backend Deployment..." -ForegroundColor Green

# Set Railway API endpoint
$railwayApiUrl = "https://api.railway.app/graphql"

# Headers for Railway API
$headers = @{
    "Authorization" = "Bearer $RailwayToken"
    "Content-Type" = "application/json"
}

# Step 1: Create Project
Write-Host "Creating Railway project..." -ForegroundColor Yellow
$createProjectQuery = @{
    query = @"
mutation {
  projectCreate(input: {name: "cleanloop-backend"}) {
    project {
      id
      name
    }
  }
}
"@
} | ConvertTo-Json

$projectResponse = Invoke-RestMethod -Uri $railwayApiUrl -Method Post -Headers $headers -Body $createProjectQuery
$projectId = $projectResponse.data.projectCreate.project.id
Write-Host "Project created: $projectId" -ForegroundColor Green

# Step 2: Create PostgreSQL Plugin
Write-Host "Creating PostgreSQL service..." -ForegroundColor Yellow
$createPostgresQuery = @{
    query = @"
mutation {
  pluginCreate(input: {projectId: "$projectId", type: POSTGRESQL}) {
    plugin {
      id
      name
    }
  }
}
"@
} | ConvertTo-Json

$postgresResponse = Invoke-RestMethod -Uri $railwayApiUrl -Method Post -Headers $headers -Body $createPostgresQuery
$postgresPluginId = $postgresResponse.data.pluginCreate.plugin.id
Write-Host "PostgreSQL created: $postgresPluginId" -ForegroundColor Green

# Step 3: Create Redis Plugin
Write-Host "Creating Redis service..." -ForegroundColor Yellow
$createRedisQuery = @{
    query = @"
mutation {
  pluginCreate(input: {projectId: "$projectId", type: REDIS}) {
    plugin {
      id
      name
    }
  }
}
"@
} | ConvertTo-Json

$redisResponse = Invoke-RestMethod -Uri $railwayApiUrl -Method Post -Headers $headers -Body $createRedisQuery
$redisPluginId = $redisResponse.data.pluginCreate.plugin.id
Write-Host "Redis created: $redisPluginId" -ForegroundColor Green

# Step 4: Connect GitHub Repo
Write-Host "Connecting GitHub repository..." -ForegroundColor Yellow
$connectRepoQuery = @{
    query = @"
mutation {
  serviceCreate(input: {
    projectId: "$projectId",
    name: "cleanloop-api",
    serviceSource: {
      type: GIT
      repo: {
        provider: GITHUB
        owner: "tatasuresh"
        name: "SwachhSanatan"
        branch: "main"
      }
    }
  }) {
    service {
      id
      name
    }
  }
}
"@
} | ConvertTo-Json

$repoResponse = Invoke-RestMethod -Uri $railwayApiUrl -Method Post -Headers $headers -Body $connectRepoQuery
$serviceId = $repoResponse.data.serviceCreate.service.id
Write-Host "Service created: $serviceId" -ForegroundColor Green

Write-Host "Railway deployment setup complete!" -ForegroundColor Green
Write-Host "Project ID: $projectId" -ForegroundColor Cyan
Write-Host "Service ID: $serviceId" -ForegroundColor Cyan
Write-Host "PostgreSQL ID: $postgresPluginId" -ForegroundColor Cyan
Write-Host "Redis ID: $redisPluginId" -ForegroundColor Cyan
