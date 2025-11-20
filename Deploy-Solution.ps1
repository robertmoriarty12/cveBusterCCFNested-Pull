# cveBuster Nested API - Automated Deployment Script
# This script automates the entire deployment process

[CmdletBinding()]
param(
    [Parameter(Mandatory=$false)]
    [string]$ResourceGroupName,
    
    [Parameter(Mandatory=$false)]
    [string]$WorkspaceName,
    
    [Parameter(Mandatory=$false)]
    [string]$SubscriptionId,
    
    [Parameter(Mandatory=$false)]
    [string]$ApiEndpoint = "http://localhost:5000",
    
    [Parameter(Mandatory=$false)]
    [string]$ApiKey = "cvebuster-nested-key",
    
    [Parameter(Mandatory=$false)]
    [switch]$GenerateDataOnly,
    
    [Parameter(Mandatory=$false)]
    [switch]$StartServerOnly,
    
    [Parameter(Mandatory=$false)]
    [switch]$PackageOnly,
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipDataGeneration,
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipServer
)

$ErrorActionPreference = "Stop"

# Colors for output
function Write-Success { param($Message) Write-Host "✅ $Message" -ForegroundColor Green }
function Write-Info { param($Message) Write-Host "ℹ️  $Message" -ForegroundColor Cyan }
function Write-Warning { param($Message) Write-Host "⚠️  $Message" -ForegroundColor Yellow }
function Write-Error { param($Message) Write-Host "❌ $Message" -ForegroundColor Red }
function Write-Step { param($Message) Write-Host "`n$Message" -ForegroundColor Yellow }

Write-Host @"
═══════════════════════════════════════════════════════════════
  cveBuster Nested API - Automated Deployment
═══════════════════════════════════════════════════════════════
"@ -ForegroundColor Cyan

# Paths
$SolutionRoot = "C:\GitHub\Azure-Sentinel\Solutions\cveBusterNestedAPI"
$ServerPath = Join-Path $SolutionRoot "Server"
$PackagingToolPath = "C:\GitHub\Azure-Sentinel\Tools\Create-Azure-Sentinel-Solution\V3"
$SolutionConfigPath = Join-Path $SolutionRoot "Data\Solution_cveBuster.json"
$PackageOutputPath = Join-Path $SolutionRoot "Package"
$MainTemplatePath = Join-Path $PackageOutputPath "mainTemplate.json"

# ═══════════════════════════════════════════════════════════════
# STEP 1: Generate Test Data
# ═══════════════════════════════════════════════════════════════
if (-not $SkipDataGeneration) {
    Write-Step "STEP 1: Generating Test Data"
    
    if (-not (Test-Path $ServerPath)) {
        Write-Error "Server directory not found: $ServerPath"
        exit 1
    }
    
    Push-Location $ServerPath
    
    try {
        Write-Info "Running generate_nested_data.py..."
        python generate_nested_data.py
        
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Data generation failed"
            exit 1
        }
        
        if ((Test-Path "vulnerabilities.json") -and (Test-Path "assets.json")) {
            Write-Success "Data generated successfully"
        } else {
            Write-Error "Data files not created"
            exit 1
        }
    }
    finally {
        Pop-Location
    }
    
    if ($GenerateDataOnly) {
        Write-Success "Data generation complete (GenerateDataOnly mode)"
        exit 0
    }
}

# ═══════════════════════════════════════════════════════════════
# STEP 2: Start Flask Server (Optional)
# ═══════════════════════════════════════════════════════════════
if ($StartServerOnly -or (-not $SkipServer)) {
    Write-Step "STEP 2: Starting Flask Server"
    
    Push-Location $ServerPath
    
    if ($StartServerOnly) {
        Write-Info "Starting Flask server (press Ctrl+C to stop)..."
        python app_nested.py
        exit 0
    }
    else {
        Write-Warning "Skipping server start (use -StartServerOnly to start manually)"
        Write-Info "To start server manually: cd $ServerPath; python app_nested.py"
    }
    
    Pop-Location
}

# ═══════════════════════════════════════════════════════════════
# STEP 3: Package Solution
# ═══════════════════════════════════════════════════════════════
Write-Step "STEP 3: Packaging Solution"

if (-not (Test-Path $PackagingToolPath)) {
    Write-Error "Packaging tool not found: $PackagingToolPath"
    exit 1
}

if (-not (Test-Path $SolutionConfigPath)) {
    Write-Error "Solution config not found: $SolutionConfigPath"
    exit 1
}

Push-Location $PackagingToolPath

try {
    Write-Info "Running createSolutionV3.ps1..."
    
    .\createSolutionV3.ps1 `
        -packageConfigPath $SolutionConfigPath `
        -outputFolderPath $PackageOutputPath
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Solution packaging failed"
        exit 1
    }
    
    if (Test-Path $MainTemplatePath) {
        Write-Success "Solution packaged successfully"
    } else {
        Write-Error "mainTemplate.json not created"
        exit 1
    }
}
finally {
    Pop-Location
}

if ($PackageOnly) {
    Write-Success "Packaging complete (PackageOnly mode)"
    exit 0
}

# ═══════════════════════════════════════════════════════════════
# STEP 4: Deploy to Azure (Optional)
# ═══════════════════════════════════════════════════════════════
if ($ResourceGroupName -and $WorkspaceName) {
    Write-Step "STEP 4: Deploying to Azure"
    
    # Check if logged in
    $context = Get-AzContext -ErrorAction SilentlyContinue
    if (-not $context) {
        Write-Info "Not logged in to Azure. Logging in..."
        Connect-AzAccount
    }
    
    # Set subscription if provided
    if ($SubscriptionId) {
        Write-Info "Setting subscription: $SubscriptionId"
        Set-AzContext -SubscriptionId $SubscriptionId
    }
    
    # Verify resource group exists
    $rg = Get-AzResourceGroup -Name $ResourceGroupName -ErrorAction SilentlyContinue
    if (-not $rg) {
        Write-Error "Resource group not found: $ResourceGroupName"
        exit 1
    }
    
    Write-Info "Deploying to Resource Group: $ResourceGroupName"
    Write-Info "Workspace: $WorkspaceName"
    Write-Info "API Endpoint: $ApiEndpoint"
    
    try {
        New-AzResourceGroupDeployment `
            -ResourceGroupName $ResourceGroupName `
            -TemplateFile $MainTemplatePath `
            -workspace $WorkspaceName `
            -apiEndpoint $ApiEndpoint `
            -apiKey $ApiKey `
            -Verbose
        
        Write-Success "Deployment complete!"
        Write-Info "Data should start flowing in 5-10 minutes"
        
        Write-Host "`nNext Steps:" -ForegroundColor Yellow
        Write-Host "1. Navigate to Sentinel → Data Connectors" -ForegroundColor White
        Write-Host "2. Find 'cveBuster Nested API (Preview)'" -ForegroundColor White
        Write-Host "3. Wait 5-10 minutes for first data" -ForegroundColor White
        Write-Host "4. Query: cveBusterNestedVulnerabilities_CL | take 10" -ForegroundColor White
    }
    catch {
        Write-Error "Deployment failed: $_"
        exit 1
    }
}
else {
    Write-Warning "Skipping Azure deployment (ResourceGroupName and WorkspaceName not provided)"
    Write-Info "To deploy manually:"
    Write-Host @"

    New-AzResourceGroupDeployment ``
      -ResourceGroupName "your-rg" ``
      -TemplateFile "$MainTemplatePath" ``
      -workspace "your-sentinel-workspace" ``
      -apiEndpoint "$ApiEndpoint" ``
      -apiKey "$ApiKey"

"@ -ForegroundColor Gray
}

# ═══════════════════════════════════════════════════════════════
# Summary
# ═══════════════════════════════════════════════════════════════
Write-Host "`n═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Deployment Summary" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan

Write-Success "Data generated: vulnerabilities.json, assets.json"
Write-Success "Solution packaged: $PackageOutputPath"

if ($ResourceGroupName -and $WorkspaceName) {
    Write-Success "Deployed to Azure: $ResourceGroupName"
}

Write-Host "`n📚 Documentation:" -ForegroundColor Yellow
Write-Host "   README.md         - Complete solution documentation" -ForegroundColor White
Write-Host "   QUICKSTART.md     - 5-minute quick start guide" -ForegroundColor White
Write-Host "   TESTING_CHECKLIST.md - 50+ validation tests" -ForegroundColor White
Write-Host "   COMPARISON.md     - Compare with pagination solution" -ForegroundColor White

Write-Host "`n🧪 Testing:" -ForegroundColor Yellow
Write-Host "   Start server:  cd $ServerPath; python app_nested.py" -ForegroundColor White
Write-Host "   Test API:      Invoke-RestMethod -Uri 'http://localhost:5000/api/stats' -Headers @{ 'Authorization' = '$ApiKey' }" -ForegroundColor White

Write-Host "`n" -NoNewline
