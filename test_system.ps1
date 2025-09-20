# PowerShell Test Script for Multi-Level Summarization System
# This script helps test the system using PowerShell commands

Write-Host "🧪 Testing Multi-Level Summarization System" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan

# Test endpoints
$endpoints = @(
    @{url="http://localhost:8000"; name="Orchestrator"},
    @{url="http://localhost:8001"; name="Server 1 (L1 Summary)"},
    @{url="http://localhost:8002"; name="Server 2 (L2 Summary)"},
    @{url="http://localhost:8003"; name="Server 3 (L3 Summary)"}
)

Write-Host "`n🏥 Step 1: Health Checks" -ForegroundColor Yellow
Write-Host "-" * 30 -ForegroundColor Yellow

$healthyServers = @()
foreach ($endpoint in $endpoints) {
    try {
        $response = Invoke-RestMethod -Uri "$($endpoint.url)/health" -Method Get -TimeoutSec 5
        Write-Host "✅ $($endpoint.name): Healthy" -ForegroundColor Green
        $healthyServers += $endpoint
    }
    catch {
        Write-Host "❌ $($endpoint.name): $($_.Exception.Message)" -ForegroundColor Red
    }
}

if ($healthyServers.Count -eq 0) {
    Write-Host "`n❌ No servers are running. Please start the system first:" -ForegroundColor Red
    Write-Host "   python manage_system.py start" -ForegroundColor Yellow
    exit
}

Write-Host "`n✅ $($healthyServers.Count) servers are healthy" -ForegroundColor Green

# Test ingestion on Server 1
Write-Host "`n📚 Step 2: Document Ingestion" -ForegroundColor Yellow
Write-Host "-" * 30 -ForegroundColor Yellow

try {
    Write-Host "Triggering PDF ingestion on Server 1..." -ForegroundColor Cyan
    $response = Invoke-RestMethod -Uri "http://localhost:8001/ingest" -Method Post -TimeoutSec 60
    Write-Host "✅ Ingestion successful!" -ForegroundColor Green
    Write-Host "   - Chunks processed: $($response.chunks)" -ForegroundColor White
    Write-Host "   - Vectors added: $($response.vectors_added)" -ForegroundColor White
    Write-Host "   - Processing time: $([math]::Round($response.processing_time, 2))s" -ForegroundColor White
}
catch {
    Write-Host "❌ Ingestion failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test L2 summarization
Write-Host "`n📝 Step 3: L2 Summarization" -ForegroundColor Yellow
Write-Host "-" * 30 -ForegroundColor Yellow

try {
    Write-Host "Creating L2 summary from L1..." -ForegroundColor Cyan
    $response = Invoke-RestMethod -Uri "http://localhost:8002/summarize_l1" -Method Post -TimeoutSec 60
    Write-Host "✅ L2 summarization successful!" -ForegroundColor Green
    Write-Host "   - L1 length: $($response.l1_length) chars" -ForegroundColor White
    Write-Host "   - L2 length: $($response.l2_length) chars" -ForegroundColor White
    Write-Host "   - Compression ratio: $([math]::Round($response.compression_ratio, 2))" -ForegroundColor White
}
catch {
    Write-Host "❌ L2 summarization failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test L3 summarization
Write-Host "`n📄 Step 4: L3 Summarization" -ForegroundColor Yellow
Write-Host "-" * 30 -ForegroundColor Yellow

try {
    Write-Host "Creating L3 summary from L2..." -ForegroundColor Cyan
    $response = Invoke-RestMethod -Uri "http://localhost:8003/summarize_l2" -Method Post -TimeoutSec 60
    Write-Host "✅ L3 summarization successful!" -ForegroundColor Green
    Write-Host "   - L2 length: $($response.l2_length) chars" -ForegroundColor White
    Write-Host "   - L3 length: $($response.l3_length) chars" -ForegroundColor White
    Write-Host "   - Compression ratio: $([math]::Round($response.compression_ratio, 2))" -ForegroundColor White
}
catch {
    Write-Host "❌ L3 summarization failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test intelligent query routing
Write-Host "`n🧠 Step 5: Intelligent Query Routing" -ForegroundColor Yellow
Write-Host "-" * 30 -ForegroundColor Yellow

$testQueries = @(
    "What are the key points about Jharkhand policies?",
    "Give me a summary of the MSME promotion policy",
    "What are the specific requirements in the industrial policy?"
)

for ($i = 0; $i -lt $testQueries.Count; $i++) {
    $query = $testQueries[$i]
    $queryNum = $i + 1
    
    try {
        Write-Host "`nQuery $queryNum : $query" -ForegroundColor Cyan
        
        $body = @{
            question = $query
        } | ConvertTo-Json
        
        $response = Invoke-RestMethod -Uri "http://localhost:8000/query" -Method Post -Body $body -ContentType "application/json" -TimeoutSec 30
        
        $server = $response.routing_info.primary_server
        $complexity = $response.routing_info.complexity
        
        Write-Host "✅ Routed to: $server ($complexity)" -ForegroundColor Green
        
        # Show answer preview
        $answer = $response.answer
        if ($answer.Length -gt 150) {
            $preview = $answer.Substring(0, 150) + "..."
        } else {
            $preview = $answer
        }
        Write-Host "💬 Answer: $preview" -ForegroundColor White
        
        # Show citations
        $citations = $response.citations.Count
        Write-Host "📚 Citations: $citations sources" -ForegroundColor White
    }
    catch {
        Write-Host "❌ Query failed: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "`n🎉 Testing completed!" -ForegroundColor Green
Write-Host "`n💡 System is ready for use!" -ForegroundColor Cyan
