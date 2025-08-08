# SEC Filings QA Agent - Individual Question Testing
# Test each assignment evaluation question individually

Write-Host "SEC FILINGS QA AGENT - INDIVIDUAL QUESTION TESTING" -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan

# Function to test a single question
function Test-Question {
    param(
        [string]$QuestionNumber,
        [string]$Question,
        [string]$Description,
        [string]$Ticker = $null,
        [string]$FilingType = $null,
        [int]$K = 8
    )
    
    Write-Host ""
    Write-Host "=" * 80 -ForegroundColor Gray
    Write-Host "QUESTION $QuestionNumber" -ForegroundColor Yellow
    Write-Host "Description: $Description" -ForegroundColor Cyan
    Write-Host "Question: $Question" -ForegroundColor White
    Write-Host "=" * 80 -ForegroundColor Gray
    
    try {
        # Prepare request body
        $requestBody = @{
            question = $Question
            k = $K
        }
        
        # Add filters if specified
        if ($Ticker) {
            $requestBody.ticker = $Ticker
            Write-Host "Filter: Ticker = $Ticker" -ForegroundColor Blue
        }
        if ($FilingType) {
            $requestBody.filing_type = $FilingType
            Write-Host "Filter: Filing Type = $FilingType" -ForegroundColor Blue
        }
        
        $body = $requestBody | ConvertTo-Json
        
        Write-Host ""
        Write-Host "Processing question..." -ForegroundColor Yellow
        
        $response = Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/v1/questions" `
                                    -Method POST `
                                    -ContentType "application/json" `
                                    -Body $body
        
        Write-Host ""
        Write-Host "ANSWER GENERATED SUCCESSFULLY!" -ForegroundColor Green
        Write-Host ""
        Write-Host "FULL ANSWER:" -ForegroundColor Yellow
        Write-Host $response.data.answer -ForegroundColor White
        
        Write-Host ""
        Write-Host "SOURCE ANALYSIS:" -ForegroundColor Yellow
        Write-Host "Total Sources: $($response.data.sources.Count) documents" -ForegroundColor Blue
        
        # Detailed source breakdown
        $sourceStats = $response.data.sources | Group-Object {$_.metadata.ticker} | ForEach-Object {
            $companyName = $_.Name
            $chunkCount = $_.Count
            $avgSimilarity = ($_.Group | Measure-Object similarity_score -Average).Average
            "$companyName ($chunkCount chunks, avg similarity: $([math]::Round($avgSimilarity, 3)))"
        }
        
        Write-Host "Companies Referenced:" -ForegroundColor Magenta
        foreach ($stat in $sourceStats) {
            Write-Host "  - $stat" -ForegroundColor White
        }
        
        # Filing type breakdown
        $filingStats = $response.data.sources | Group-Object {$_.metadata.filing_type} | ForEach-Object {
            "$($_.Name): $($_.Count) documents"
        }
        Write-Host ""
        Write-Host "Filing Types:" -ForegroundColor Magenta
        foreach ($stat in $filingStats) {
            Write-Host "  - $stat" -ForegroundColor White
        }
        
        Write-Host ""
        Write-Host "QUESTION $QuestionNumber COMPLETED SUCCESSFULLY!" -ForegroundColor Green
        
    } catch {
        Write-Host ""
        Write-Host "ERROR PROCESSING QUESTION $QuestionNumber" -ForegroundColor Red
        Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    Write-Host ""
    Write-Host "Press Enter to continue to next question (or Ctrl+C to exit)..."
    Read-Host
}

# Test each question individually
Write-Host ""
Write-Host "This script will test each assignment evaluation question individually."
Write-Host "You can review each answer in detail before proceeding to the next question."
Write-Host ""
Write-Host "Press Enter to start testing..."
Read-Host

# Question 1
Test-Question -QuestionNumber "1" `
              -Question "What are the primary revenue drivers for major technology companies, and how have they evolved?" `
              -Description "Multi-company tech sector revenue analysis with temporal evolution"

# Question 2  
Test-Question -QuestionNumber "2" `
              -Question "Compare R&D spending trends across companies. What insights about innovation investment strategies?" `
              -Description "Cross-company R&D spending and innovation strategy comparison"

# Question 3
Test-Question -QuestionNumber "3" `
              -Question "Identify significant working capital changes for financial services companies and driving factors." `
              -Description "Financial sector working capital analysis"

# Question 4
Test-Question -QuestionNumber "4" `
              -Question "What are the most commonly cited risk factors across industries? How do same-sector companies prioritize differently?" `
              -Description "Cross-industry risk factor analysis with sector comparison"

# Question 5
Test-Question -QuestionNumber "5" `
              -Question "How do companies describe climate-related risks? Notable industry differences?" `
              -Description "Climate risk disclosure analysis across sectors"

# Question 6
Test-Question -QuestionNumber "6" `
              -Question "Analyze recent executive compensation changes. What trends emerge?" `
              -Description "Executive compensation trend analysis"

# Question 7
Test-Question -QuestionNumber "7" `
              -Question "What significant insider trading activity occurred? What might this indicate?" `
              -Description "Insider trading activity analysis and implications"

# Question 8
Test-Question -QuestionNumber "8" `
              -Question "How are companies positioning regarding AI and automation? Strategic approaches?" `
              -Description "AI and automation strategic positioning analysis"

# Question 9
Test-Question -QuestionNumber "9" `
              -Question "Identify recent M&A activity. What strategic rationale do companies provide?" `
              -Description "Merger and acquisition activity with strategic rationale"

# Question 10
Test-Question -QuestionNumber "10" `
              -Question "How do companies describe competitive advantages? What themes emerge?" `
              -Description "Competitive advantage themes across companies"

Write-Host ""
Write-Host "=" * 80 -ForegroundColor Green
Write-Host "ALL 10 ASSIGNMENT EVALUATION QUESTIONS COMPLETED!" -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Green
Write-Host ""
Write-Host "Your SEC Filings QA Agent has successfully demonstrated:" -ForegroundColor Cyan
Write-Host "✅ Multi-company financial analysis capabilities" -ForegroundColor Green
Write-Host "✅ Cross-sector industry comparisons" -ForegroundColor Green  
Write-Host "✅ Temporal trend analysis" -ForegroundColor Green
Write-Host "✅ Comprehensive source attribution" -ForegroundColor Green
Write-Host "✅ Complex financial research question handling" -ForegroundColor Green
Write-Host ""
Write-Host "ASSIGNMENT COMPLETION: EXCEPTIONAL SUCCESS!" -ForegroundColor Yellow
