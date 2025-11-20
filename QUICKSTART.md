# cveBuster Nested API - Quick Start Guide

## 🚀 Quick Start (5 Minutes)

### Step 1: Generate Test Data
```powershell
cd C:\GitHub\Azure-Sentinel\Solutions\cveBusterNestedAPI\Server
python generate_nested_data.py
```

**Expected Output:**
```
Generating nested API test data...
============================================================

1. Generating 30 asset records...
   ✅ Created assets.json with 30 assets

2. Generating 50 vulnerability records...
   ✅ Created vulnerabilities.json with 50 vulnerabilities
      - Recent (last 5 min): 15
      - Old (30-90 days): 35

3. Relationship Statistics:
   - Total vuln → asset relationships: 150
   - Average assets per vulnerability: 3.0
   - Expected API calls per poll cycle:
     * Step 0 (Get IDs): 1 call
     * Step 1 (Vuln details): 15 calls
     * Step 2 (Asset details): ~45 calls
     * TOTAL: ~61 API calls

============================================================
✅ Data generation complete!
```

### Step 2: Start Mock API Server
```powershell
python app_nested.py
```

**Expected Output:**
```
======================================================================
🚀 cveBuster Nested API Server
======================================================================

✅ Loaded 50 vulnerabilities
✅ Loaded 30 assets

📡 API Endpoints:
   Step 0: GET /api/vulnerabilities/ids?startTime=<iso>&endTime=<iso>
   Step 1: GET /api/vulnerabilities/<vuln_id>
   Step 2: GET /api/assets/<asset_name>
   Stats:  GET /api/stats

🔑 Authentication:
   Header: Authorization: cvebuster-nested-key

======================================================================
🟢 Server starting on http://0.0.0.0:5000
======================================================================
```

### Step 3: Test API Endpoints Manually

Open a new PowerShell window and test each endpoint:

```powershell
# Set API key
$headers = @{ "Authorization" = "cvebuster-nested-key" }

# Test Step 0: Get vulnerability IDs
$startTime = (Get-Date).AddMinutes(-10).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
$endTime = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
Invoke-RestMethod -Uri "http://localhost:5000/api/vulnerabilities/ids?startTime=$startTime&endTime=$endTime" -Headers $headers

# Test Step 1: Get vulnerability details (use an ID from above)
Invoke-RestMethod -Uri "http://localhost:5000/api/vulnerabilities/CVE-2024-10001" -Headers $headers

# Test Step 2: Get asset details (use an asset name from above)
Invoke-RestMethod -Uri "http://localhost:5000/api/assets/SRV-WEB-001" -Headers $headers

# Get stats
Invoke-RestMethod -Uri "http://localhost:5000/api/stats" -Headers $headers
```

### Step 4: Verify Nested API Flow

Watch the Flask server logs to see the nested call pattern:

**Expected Log Output:**
```
[STEP 0] GET /api/vulnerabilities/ids
         TimeFilter: 2025-11-18T10:00:00Z to 2025-11-18T10:10:00Z
         Returned 15 IDs

[STEP 1] GET /api/vulnerabilities/CVE-2024-10001
         Severity: Critical, Affected Assets: 3

[STEP 2] GET /api/assets/SRV-WEB-001
         OS: Windows Server 2022, Patch Status: Missing Critical Patches

[STEP 2] GET /api/assets/SRV-APP-005
         OS: Ubuntu 22.04 LTS, Patch Status: Up to Date

[STEP 2] GET /api/assets/SRV-DB-002
         OS: Windows Server 2019, Patch Status: Missing Critical Patches
```

## 📦 Package Solution for Sentinel

### Step 5: Create Solution Package
```powershell
cd C:\GitHub\Azure-Sentinel\Tools\Create-Azure-Sentinel-Solution\V3

.\createSolutionV3.ps1 `
  -packageConfigPath "C:\GitHub\Azure-Sentinel\Solutions\cveBusterNestedAPI\Data\Solution_cveBuster.json" `
  -outputFolderPath "C:\GitHub\Azure-Sentinel\Solutions\cveBusterNestedAPI\Package"
```

**Expected Output:**
```
Processing solution: cveBuster Nested API Testing Solution
Processing Data Connector: cveBuster_connectorDefinition.json
Processing Data Connector: cveBuster_PollerConfig.json
Creating mainTemplate.json
Creating createUiDefinition.json
Creating package zip: 3.0.0.zip

✅ Solution package created successfully!
```

## 🌩️ Deploy to Sentinel

### Option A: Deploy with PowerShell

```powershell
# Login to Azure
Connect-AzAccount

# Set context
Set-AzContext -SubscriptionId "your-subscription-id"

# Deploy solution
New-AzResourceGroupDeployment `
  -ResourceGroupName "your-rg-name" `
  -TemplateFile "C:\GitHub\Azure-Sentinel\Solutions\cveBusterNestedAPI\Package\mainTemplate.json" `
  -workspace "your-sentinel-workspace-name" `
  -apiEndpoint "http://YOUR_SERVER_IP:5000" `
  -apiKey "cvebuster-nested-key"
```

### Option B: Deploy via Azure Portal

1. Navigate to Azure Portal → Sentinel → Content Hub
2. Click "Import" → Upload `Package/3.0.0.zip`
3. Follow the wizard to configure:
   - **API Endpoint**: `http://YOUR_SERVER_IP:5000`
   - **API Key**: `cvebuster-nested-key`
4. Click "Create"

## 🔍 Verify in Sentinel

### Step 6: Wait for First Poll (5-10 minutes)

CCF polls every 5 minutes. Wait for the first poll cycle to complete.

### Step 7: Query Ingested Data

```kql
// Check if data is arriving
cveBusterNestedVulnerabilities_CL
| take 10

// View joined vulnerability and asset data
cveBusterNestedVulnerabilities_CL
| extend vuln = parse_json(vulnerability_details)
| extend vuln_id = tostring(vuln.vuln_id)
| extend severity = tostring(vuln.severity)
| extend cvss = toreal(vuln.cvss)
| extend affected_assets = parse_json(assets)
| mv-expand affected_assets
| extend asset_name = tostring(affected_assets.asset_name)
| extend os_version = tostring(affected_assets.os_version)
| extend patch_status = tostring(affected_assets.patch_status)
| project TimeGenerated, vuln_id, severity, cvss, asset_name, os_version, patch_status
| order by cvss desc

// Count vulnerabilities by severity
cveBusterNestedVulnerabilities_CL
| summarize count() by vulnerability_severity

// Find critical vulnerabilities on unpatched Windows servers
cveBusterNestedVulnerabilities_CL
| where vulnerability_severity == "Critical"
| extend affected_assets = parse_json(assets)
| mv-expand affected_assets
| extend asset_name = tostring(affected_assets.asset_name)
| extend os_version = tostring(affected_assets.os_version)
| extend patch_status = tostring(affected_assets.patch_status)
| where os_version contains "Windows" and patch_status contains "Missing"
| project vulnerability_id, vulnerability_cvss, asset_name, os_version, patch_status
```

## 🧪 Validation Tests

### Test 1: Verify Nested API Calls
**Objective**: Confirm all 3 levels execute correctly

1. Check Flask logs for Step 0, Step 1, Step 2 calls
2. Count total API calls (should be: 1 + recent_vulns + total_assets)
3. Verify no 404 errors in logs

### Test 2: Verify Data Joining
**Objective**: Confirm `shouldJoinNestedData` works

```kql
cveBusterNestedVulnerabilities_CL
| extend vuln = parse_json(vulnerability_details)
| extend assets_array = parse_json(assets)
| extend vuln_id = tostring(vuln.vuln_id)
| extend asset_count = array_length(assets_array)
| where asset_count > 0
| project vuln_id, asset_count, vulnerability_details, assets
| take 5
```

**Expected**: Each record has:
- `vulnerability_details`: Full vulnerability object
- `assets`: Array of asset objects
- No null values

### Test 3: Verify Time Filtering
**Objective**: Only recent vulnerabilities are fetched

```kql
cveBusterNestedVulnerabilities_CL
| extend vuln = parse_json(vulnerability_details)
| extend last_modified = todatetime(vuln.last_modified)
| summarize 
    oldest = min(last_modified),
    newest = max(last_modified),
    count = count()
| extend time_range_minutes = datetime_diff('minute', newest, oldest)
```

**Expected**: `time_range_minutes` should be ~5 (matching queryWindowInMin)

### Test 4: Verify Fan-Out Pattern
**Objective**: 1 vulnerability → many asset calls

Check Flask logs:
```
[STEP 1] GET /api/vulnerabilities/CVE-2024-10001
         Severity: Critical, Affected Assets: 5
[STEP 2] GET /api/assets/SRV-WEB-001   <-- 5 separate calls
[STEP 2] GET /api/assets/SRV-APP-002
[STEP 2] GET /api/assets/SRV-DB-003
[STEP 2] GET /api/assets/SRV-FILE-004
[STEP 2] GET /api/assets/SRV-MAIL-005
```

## 🐛 Troubleshooting

### Issue: No data in Sentinel after 10 minutes

**Check CCF Logs**:
```kql
LAQueryLogs
| where RequestTarget contains "cveBusterNestedAPI"
| order by TimeGenerated desc
```

**Common Causes**:
1. API endpoint unreachable (firewall/network issue)
2. Incorrect API key
3. No recent vulnerabilities in last 5 minutes (regenerate data)

### Issue: Only Step 0 data, no nested calls

**Verify KQL parsing**:
```kql
// Test placeholder extraction manually
let sample_response = '{"vulnerability_ids": ["CVE-2024-10001", "CVE-2024-10002"]}';
let source = datatable(data:string) [sample_response];
source 
| project res = parse_json(data) 
| project ids = res['vulnerability_ids'] 
| mvexpand ids 
| project Url_PlaceHolder = ids
```

**Expected**: Table with 2 rows: `CVE-2024-10001`, `CVE-2024-10002`

### Issue: Assets not joined into vulnerability records

**Check DCR transformation**:
- Verify `shouldJoinNestedData: true` in Step 1 and Step 2
- Verify `joinedDataStepName` matches field names in query
- Check if `assets` field is `dynamic` type (not string)

## 📊 Expected Results

After successful deployment and first poll:

| Metric | Expected Value |
|--------|---------------|
| API calls per poll | ~61 (1 + 15 + 45) |
| Records ingested | ~15 (recent vulnerabilities) |
| Avg assets per vuln | 3.0 |
| Time to first data | 5-10 minutes |
| Poll frequency | Every 5 minutes |

## 🎓 Next Steps

1. **Extend to 4-5 levels**: Add patch details or threat intel enrichment
2. **Test async APIs**: Combine with `AsyncJobStart` / `AsyncJobWait`
3. **Test error handling**: Simulate 404s, timeouts, rate limits
4. **Scale testing**: Generate 500 vulnerabilities, 100 assets
5. **Production readiness**: Add authentication, HTTPS, logging

## 📚 References

- **README.md**: Full solution documentation
- **PIF-2025-0019**: ISV nested API requirements
- **Server/app_nested.py**: Mock API implementation
- **Data Connectors/cveBuster_PollerConfig.json**: CCF configuration

---

**Need Help?**
- Review Flask logs for API call patterns
- Check CCF logs in Azure Monitor
- Test endpoints manually with PowerShell
- Validate KQL parsing with sample data
