# SEC Filings QA Agent - Batch Company Processing Script
# Priority-based scaling to meet assignment requirements

Write-Host "SEC FILINGS QA AGENT - BATCH PROCESSING" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

# Define companies by priority and sector
$FinancialCompanies = @("JPM")
$HealthcareCompanies = @("JNJ", "PFE")
$ConsumerCompanies = @("PG", "KO")
$IndustrialCompanies = @("GE", "CAT")

# Priority 1: Complete Tech Sector (already have AAPL, MSFT)
Write-Host ""
Write-Host "PRIORITY 1: Major Tech Companies" -ForegroundColor Yellow
Write-Host "Already processed: AAPL, MSFT" -ForegroundColor Green
Write-Host "Processing remaining tech companies..." -ForegroundColor Green

foreach ($ticker in $TechCompanies) {
    Write-Host ""
    Write-Host "Processing $ticker..." -ForegroundColor Cyan
    
    try {
        # Process 10-K filings (most important for financial analysis)
        $body1 = '{"filing_type": "10-K", "limit": 2}'
        $response = Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/v1/companies/$ticker/process" -Method POST -ContentType "application/json" -Body $body1
        
        Write-Host "Success $ticker 10-K: $($response.data.total_chunks_created) chunks" -ForegroundColor Green
        
        # Brief pause to avoid overwhelming the API
        Start-Sleep -Seconds 2
        
        # Also process 10-Q for quarterly data
        $body2 = '{"filing_type": "10-Q", "limit": 1}'
        $response2 = Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/v1/companies/$ticker/process" -Method POST -ContentType "application/json" -Body $body2
        
        Write-Host "Success $ticker 10-Q: $($response2.data.total_chunks_created) chunks" -ForegroundColor Green
        
    } catch {
        Write-Host "Error processing $ticker : $($_.Exception.Message)" -ForegroundColor Red
    }
    
    Start-Sleep -Seconds 3
}

# Priority 2: Financial Sector
Write-Host ""
Write-Host "PRIORITY 2: Financial Companies" -ForegroundColor Yellow

foreach ($ticker in $FinancialCompanies[0..2]) {
    Write-Host ""
    Write-Host "Processing $ticker..." -ForegroundColor Cyan
    
    try {
        $body = '{"filing_type": "10-K", "limit": 2}'
        $response = Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/v1/companies/$ticker/process" -Method POST -ContentType "application/json" -Body $body
        
        Write-Host "Success $ticker : $($response.data.total_chunks_created) chunks" -ForegroundColor Green
        
    } catch {
        Write-Host "Error processing $ticker : $($_.Exception.Message)" -ForegroundColor Red
    }
    
    Start-Sleep -Seconds 3
}

# Priority 3: Healthcare Sector
Write-Host ""
Write-Host "PRIORITY 3: Healthcare Companies" -ForegroundColor Yellow

foreach ($ticker in $HealthcareCompanies[0..2]) {
    Write-Host ""
    Write-Host "Processing $ticker..." -ForegroundColor Cyan
    
    try {
        $body = '{"filing_type": "10-K", "limit": 2}'
        $response = Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/v1/companies/$ticker/process" -Method POST -ContentType "application/json" -Body $body
        
        Write-Host "Success $ticker : $($response.data.total_chunks_created) chunks" -ForegroundColor Green
        
    } catch {
        Write-Host "Error processing $ticker : $($_.Exception.Message)" -ForegroundColor Red
    }
    
    Start-Sleep -Seconds 3
}

# Check system status after processing
Write-Host ""
Write-Host "CHECKING FINAL SYSTEM STATUS..." -ForegroundColor Cyan
try {
    $status = Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/v1/status" -Method GET
    Write-Host "Total Vectors: $($status.data.vector_database.total_vectors)" -ForegroundColor Green
    Write-Host "Total Companies: $($status.data.database.companies)" -ForegroundColor Green
    Write-Host "Total Filings: $($status.data.database.filings)" -ForegroundColor Green
} catch {
    Write-Host "Error checking status: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "BATCH PROCESSING COMPLETE!" -ForegroundColor Green
Write-Host "Ready to test multi-company analysis capabilities!" -ForegroundColor Cyan
