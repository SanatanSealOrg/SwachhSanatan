# CREDENTIALS TEMPLATE
# Fill in your actual credentials and save as credentials.ps1

# Railway API Token - Get from: https://dashboard.railway.app/account/tokens
$RailwayToken = "YOUR_RAILWAY_API_TOKEN_HERE"

# Vercel API Token - Get from: https://vercel.com/account/tokens
$VercelToken = "YOUR_VERCEL_API_TOKEN_HERE"

# OpenAI API Key - Get from: https://platform.openai.com/api-keys
$OpenAIKey = "sk-YOUR_OPENAI_KEY_HERE"

# AWS Credentials (optional - can use test keys)
$AwsAccessKey = "YOUR_AWS_ACCESS_KEY_HERE"
$AwsSecretKey = "YOUR_AWS_SECRET_KEY_HERE"

# Email credentials for SMTP (optional)
$SmtpUser = "your-email@gmail.com"
$SmtpPassword = "your-app-password"

# Run deployment
. .\deploy-orchestrator.ps1 -RailwayToken $RailwayToken `
    -VercelToken $VercelToken `
    -OpenAIKey $OpenAIKey `
    -AwsAccessKey $AwsAccessKey `
    -AwsSecretKey $AwsSecretKey `
    -SmtpUser $SmtpUser `
    -SmtpPassword $SmtpPassword
