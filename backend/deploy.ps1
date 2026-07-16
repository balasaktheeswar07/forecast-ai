# PowerShell script to deploy S3 buckets and DynamoDB tables to LocalStack (or standard AWS)

$Endpoint = "http://localhost:4566"
$Region = "us-east-1"

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "Deploying forecast-ai Serverless Infrastructure" -ForegroundColor Cyan
Write-Host "Target Endpoint: $Endpoint" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

# 1. Check if LocalStack is reachable
Try {
    $response = Invoke-WebRequest -Uri "$Endpoint/health" -Method Get -TimeoutSec 3 -UseBasicParsing
    Write-Host "[OK] LocalStack is online and responsive." -ForegroundColor Green
} Catch {
    Write-Host "[WARNING] Could not connect to LocalStack on $Endpoint." -ForegroundColor Yellow
    Write-Host "Make sure Docker and LocalStack are running (e.g. 'localstack start')." -ForegroundColor Yellow
    Write-Host "Proceeding with resource creation attempts anyway..." -ForegroundColor Yellow
}

# 2. Create S3 Buckets
Write-Host "`nCreating S3 Buckets..." -ForegroundColor Green
$buckets = @("forecast-ai-datasets", "forecast-ai-reports")

foreach ($bucket in $buckets) {
    Write-Host "Configuring S3 Bucket: $bucket..."
    # Check if bucket exists
    $check = aws --endpoint-url=$Endpoint s3api head-bucket --bucket $bucket 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "-> S3 Bucket '$bucket' already exists." -ForegroundColor Yellow
    } else {
        aws --endpoint-url=$Endpoint s3 mb "s3://$bucket" --region $Region
        if ($LASTEXITCODE -eq 0) {
            Write-Host "-> S3 Bucket '$bucket' created successfully." -ForegroundColor Green
        } else {
            Write-Host "-> Failed to create S3 Bucket '$bucket'." -ForegroundColor Red
        }
    }
}

# 3. Create DynamoDB Table
Write-Host "`nConfiguring DynamoDB Table: forecast-ai-campaigns..." -ForegroundColor Green
$tableCheck = aws --endpoint-url=$Endpoint dynamodb describe-table --table-name forecast-ai-campaigns 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "-> Table 'forecast-ai-campaigns' already exists." -ForegroundColor Yellow
} else {
    aws --endpoint-url=$Endpoint dynamodb create-table `
        --table-name forecast-ai-campaigns `
        --attribute-definitions AttributeName=campaign_id,AttributeType=S `
        --key-schema AttributeName=campaign_id,KeyType=HASH `
        --billing-mode PAY_PER_REQUEST `
        --region $Region
        
    if ($LASTEXITCODE -eq 0) {
        Write-Host "-> DynamoDB table 'forecast-ai-campaigns' created successfully." -ForegroundColor Green
    } else {
        Write-Host "-> Failed to create DynamoDB table." -ForegroundColor Red
    }
}

Write-Host "`n=============================================" -ForegroundColor Cyan
Write-Host "Deployment Checklist Complete!" -ForegroundColor Cyan
Write-Host "Start the backend server using:" -ForegroundColor Gray
Write-Host "  python run_backend.py" -ForegroundColor Gray
Write-Host "=============================================" -ForegroundColor Cyan
