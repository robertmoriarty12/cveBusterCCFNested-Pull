<#
.SYNOPSIS
    Regenerates test data and provides restart instructions for the Flask server.
.DESCRIPTION
    Regenerates vulnerabilities.json and assets.json with fresh timestamps (30% recent data).
    Provides instructions for restarting the Flask server on the remote VM.
.EXAMPLE
    .\Restart-TestServer.ps1
#>

Write-Host "Regenerating test data with fresh timestamps..." -ForegroundColor Cyan

try {
    python generate_nested_data.py
    Write-Host "✅ Data regenerated successfully" -ForegroundColor Green
    Write-Host ""
    
    if (Test-Path "vulnerabilities.json" -PathType Leaf) {
        $vulns = Get-Content "vulnerabilities.json" | ConvertFrom-Json
        Write-Host "   Vulnerabilities: $($vulns.Count)" -ForegroundColor Gray
    }
    
    if (Test-Path "assets.json" -PathType Leaf) {
        $assets = Get-Content "assets.json" | ConvertFrom-Json
        Write-Host "   Assets: $($assets.Count)" -ForegroundColor Gray
    }
    
    Write-Host ""
    Write-Host "📋 Next steps for VM:" -ForegroundColor Yellow
    Write-Host "   1. Transfer updated files to VM (if running locally):" -ForegroundColor Gray
    Write-Host "      scp vulnerabilities.json assets.json rmoriarty@20.29.43.115:~/cveBusterCCFNested-Pull/Server/" -ForegroundColor White
    Write-Host ""
    Write-Host "   2. On the VM, restart Flask:" -ForegroundColor Gray
    Write-Host "      cd ~/cveBusterCCFNested-Pull/Server" -ForegroundColor White
    Write-Host "      # Ctrl+C to stop current server" -ForegroundColor White
    Write-Host "      python3 app_nested.py" -ForegroundColor White
    Write-Host ""
    Write-Host "   3. Re-run the test:" -ForegroundColor Gray
    Write-Host "      cd C:\GitHub\Azure-Sentinel\Solutions\cveBusterNestedAPI" -ForegroundColor White
    Write-Host "      .\Test-NestedAPI.ps1 -BaseUrl http://20.29.43.115:5000 -MinutesBack 10" -ForegroundColor White
    
} catch {
    Write-Host "❌ Failed to regenerate data" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "   Make sure you're in the Server directory and Python is available." -ForegroundColor Gray
}
