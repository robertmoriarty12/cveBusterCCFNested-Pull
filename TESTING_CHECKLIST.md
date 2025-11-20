# cveBuster Nested API - Testing Checklist

## 📋 Pre-Deployment Testing

### ✅ Local API Server Testing

- [ ] **Test 1.1**: Generate data successfully
  ```powershell
  python generate_nested_data.py
  # Verify: vulnerabilities.json and assets.json created
  # Verify: 30% recent, 70% old distribution
  ```

- [ ] **Test 1.2**: Start Flask server without errors
  ```powershell
  python app_nested.py
  # Verify: "Loaded 50 vulnerabilities" message
  # Verify: "Loaded 30 assets" message
  # Verify: Server running on port 5000
  ```

- [ ] **Test 1.3**: Test Step 0 - Get vulnerability IDs
  ```powershell
  $headers = @{ "Authorization" = "cvebuster-nested-key" }
  $now = (Get-Date).ToUniversalTime()
  $start = $now.AddMinutes(-10).ToString("yyyy-MM-ddTHH:mm:ssZ")
  $end = $now.ToString("yyyy-MM-ddTHH:mm:ssZ")
  Invoke-RestMethod -Uri "http://localhost:5000/api/vulnerabilities/ids?startTime=$start&endTime=$end" -Headers $headers
  # Verify: Returns JSON with "vulnerability_ids" array
  # Verify: Count > 0 (should be ~15 recent IDs)
  ```

- [ ] **Test 1.4**: Test Step 1 - Get vulnerability details
  ```powershell
  Invoke-RestMethod -Uri "http://localhost:5000/api/vulnerabilities/CVE-2024-10001" -Headers $headers
  # Verify: Returns full vulnerability object
  # Verify: "affected_assets" is an array with 1-5 asset names
  ```

- [ ] **Test 1.5**: Test Step 2 - Get asset details
  ```powershell
  Invoke-RestMethod -Uri "http://localhost:5000/api/assets/SRV-WEB-001" -Headers $headers
  # Verify: Returns asset object with os_version, patch_status, etc.
  ```

- [ ] **Test 1.6**: Test authentication failure
  ```powershell
  Invoke-RestMethod -Uri "http://localhost:5000/api/stats" -Headers @{ "Authorization" = "wrong-key" }
  # Verify: Returns 401 Unauthorized
  ```

- [ ] **Test 1.7**: Verify time filtering works
  ```powershell
  # Request old time range (should return 0 IDs)
  $oldStart = $now.AddDays(-100).ToString("yyyy-MM-ddTHH:mm:ssZ")
  $oldEnd = $now.AddDays(-99).ToString("yyyy-MM-ddTHH:mm:ssZ")
  $result = Invoke-RestMethod -Uri "http://localhost:5000/api/vulnerabilities/ids?startTime=$oldStart&endTime=$oldEnd" -Headers $headers
  # Verify: $result.count -eq 0
  ```

### ✅ CCF Configuration Validation

- [ ] **Test 2.1**: Validate PollerConfig JSON syntax
  ```powershell
  Get-Content "Data Connectors/cveBusterNestedAPI_ccf/cveBuster_PollerConfig.json" | ConvertFrom-Json
  # Verify: No JSON parsing errors
  ```

- [ ] **Test 2.2**: Verify stepInfo structure
  - [ ] Root step has `stepType: "Nested"`
  - [ ] Root step has `nextSteps` array with `stepId: "step1_vulnerability_details"`
  - [ ] Step 1 has `shouldJoinNestedData: true` and `joinedDataStepName: "vulnerability"`
  - [ ] Step 1 has nested `stepInfo` pointing to Step 2
  - [ ] Step 2 has `shouldJoinNestedData: true` and `joinedDataStepName: "assets"`

- [ ] **Test 2.3**: Verify KQL placeholder parsing
  ```kql
  // Test Step 0 → Step 1 KQL
  let sample = '{"vulnerability_ids": ["CVE-2024-10001", "CVE-2024-10002"]}';
  let source = datatable(data:string) [sample];
  source 
  | project res = parse_json(data) 
  | project ids = res['vulnerability_ids'] 
  | mvexpand ids 
  | project Url_PlaceHolder = ids
  // Verify: Returns 2 rows with CVE IDs
  ```

  ```kql
  // Test Step 1 → Step 2 KQL
  let sample = '{"affected_assets": ["SRV-WEB-001", "SRV-APP-005"]}';
  let source = datatable(data:string) [sample];
  source 
  | project res = parse_json(data) 
  | project assets = res['affected_assets'] 
  | mvexpand assets 
  | project Asset_PlaceHolder = assets
  // Verify: Returns 2 rows with asset names
  ```

- [ ] **Test 2.4**: Validate DCR transformation KQL
  ```kql
  // Verify DCR KQL can parse joined data
  let sample = '{"vulnerability": {"vuln_id": "CVE-2024-10001", "severity": "Critical"}, "assets": [{"asset_name": "SRV-001"}]}';
  let source = datatable(data:string) [sample];
  source 
  | extend vuln = parse_json(data).vulnerability
  | extend vulnerability_id = tostring(vuln.vuln_id)
  | extend vulnerability_severity = tostring(vuln.severity)
  // Verify: Extracts fields correctly
  ```

## 🌩️ Azure Deployment Testing

### ✅ Solution Packaging

- [ ] **Test 3.1**: Package solution successfully
  ```powershell
  cd C:\GitHub\Azure-Sentinel\Tools\Create-Azure-Sentinel-Solution\V3
  .\createSolutionV3.ps1 -packageConfigPath "C:\GitHub\Azure-Sentinel\Solutions\cveBusterNestedAPI\Data\Solution_cveBuster.json" -outputFolderPath "C:\GitHub\Azure-Sentinel\Solutions\cveBusterNestedAPI\Package"
  # Verify: mainTemplate.json, createUiDefinition.json, 3.0.0.zip created
  ```

- [ ] **Test 3.2**: Validate mainTemplate.json
  ```powershell
  Get-Content "Package/mainTemplate.json" | ConvertFrom-Json
  # Verify: No JSON errors
  # Verify: Contains data connector resources
  # Verify: Contains DCR resources
  ```

### ✅ Sentinel Deployment

- [ ] **Test 4.1**: Deploy solution to Sentinel
  ```powershell
  New-AzResourceGroupDeployment `
    -ResourceGroupName "your-rg" `
    -TemplateFile "Package/mainTemplate.json" `
    -workspace "your-sentinel-workspace" `
    -apiEndpoint "http://YOUR_IP:5000" `
    -apiKey "cvebuster-nested-key"
  # Verify: Deployment succeeds
  # Verify: No ARM template errors
  ```

- [ ] **Test 4.2**: Verify data connector created
  - [ ] Navigate to Sentinel → Data Connectors
  - [ ] Find "cveBuster Nested API (Preview)"
  - [ ] Verify status shows "Connected" after 5-10 minutes

- [ ] **Test 4.3**: Verify DCR created
  - [ ] Navigate to Azure Monitor → Data Collection Rules
  - [ ] Find DCR for cveBusterNestedAPI
  - [ ] Verify destinations include Log Analytics workspace

- [ ] **Test 4.4**: Verify custom table created
  - [ ] Navigate to Log Analytics workspace → Tables
  - [ ] Find `cveBusterNestedVulnerabilities_CL`
  - [ ] Verify schema includes `vulnerability_details` and `assets` (dynamic)

## 🔍 Data Ingestion Testing

### ✅ First Poll Cycle (Wait 5-10 minutes)

- [ ] **Test 5.1**: Verify data arrives in Sentinel
  ```kql
  cveBusterNestedVulnerabilities_CL
  | take 10
  // Verify: Returns records
  // Verify: TimeGenerated is recent
  ```

- [ ] **Test 5.2**: Verify joined data structure
  ```kql
  cveBusterNestedVulnerabilities_CL
  | take 1
  | extend vuln = parse_json(vulnerability_details)
  | extend assets_array = parse_json(assets)
  | project vulnerability_details, assets, vuln, assets_array
  // Verify: vulnerability_details is populated JSON
  // Verify: assets is populated array
  // Verify: No null values
  ```

- [ ] **Test 5.3**: Count records ingested
  ```kql
  cveBusterNestedVulnerabilities_CL
  | where TimeGenerated > ago(15m)
  | summarize count()
  // Verify: Count ~15 (matches recent vulnerabilities)
  ```

- [ ] **Test 5.4**: Verify mv-expand works
  ```kql
  cveBusterNestedVulnerabilities_CL
  | take 1
  | extend affected_assets = parse_json(assets)
  | mv-expand affected_assets
  | project vulnerability_id, asset_name = tostring(affected_assets.asset_name)
  // Verify: Multiple rows per vulnerability
  // Verify: Each row has different asset_name
  ```

### ✅ API Call Pattern Validation

- [ ] **Test 6.1**: Check Flask logs for nested calls
  - [ ] Verify `[STEP 0]` log appears once per poll
  - [ ] Verify `[STEP 1]` logs appear ~15 times
  - [ ] Verify `[STEP 2]` logs appear ~45 times
  - [ ] Verify no 404 or 500 errors

- [ ] **Test 6.2**: Verify time filtering in API logs
  ```
  [STEP 0] TimeFilter: 2025-11-18T10:00:00Z to 2025-11-18T10:05:00Z
  ```
  - [ ] Verify startTime and endTime are 5 minutes apart
  - [ ] Verify times are recent (within last 10 minutes)

- [ ] **Test 6.3**: Verify fan-out pattern
  ```
  [STEP 1] CVE-2024-10001 - Affected Assets: 3
  [STEP 2] GET /api/assets/SRV-WEB-001
  [STEP 2] GET /api/assets/SRV-APP-005
  [STEP 2] GET /api/assets/SRV-DB-002
  ```
  - [ ] Verify number of Step 2 calls matches affected_assets count

## 🎯 Feature Validation

### ✅ Nested API Features

- [ ] **Feature 1**: Multi-level nesting (3 levels)
  - [ ] Step 0 (root) executes
  - [ ] Step 1 (nested) executes for each ID from Step 0
  - [ ] Step 2 (nested) executes for each asset from Step 1

- [ ] **Feature 2**: Data joining (`shouldJoinNestedData`)
  - [ ] Step 1 data embedded as `vulnerability` in final record
  - [ ] Step 2 data embedded as `assets` array in final record
  - [ ] No data loss between API calls

- [ ] **Feature 3**: KQL placeholder extraction
  - [ ] `Url_PlaceHolder` correctly extracted from Step 0
  - [ ] `Asset_PlaceHolder` correctly extracted from Step 1
  - [ ] Placeholders used in API URLs

- [ ] **Feature 4**: Fan-out pattern (1 → many)
  - [ ] 1 vulnerability → multiple asset API calls
  - [ ] All assets joined into single vulnerability record

- [ ] **Feature 5**: Time-based filtering
  - [ ] Only recent vulnerabilities fetched (last 5 minutes)
  - [ ] No old data in Sentinel table

### ✅ ISV Pattern Validation

- [ ] **CrowdStrike Pattern**: List IDs → Get details → Get context
  - [ ] Mimicked successfully with vulns → vuln details → assets

- [ ] **TrendMicro Pattern**: Incidents → Details → Enrichment
  - [ ] Mimicked successfully with 3-level nesting

- [ ] **SecurityScorecard Pattern**: Portfolios → Companies → Ratings
  - [ ] Fan-out pattern validated

- [ ] **BigID Pattern**: Cases → Objects → Data source
  - [ ] Validated, but array flattening requires KQL `mv-expand`

## 🐛 Error Handling Testing

### ✅ Negative Tests

- [ ] **Test 7.1**: Invalid API key
  - [ ] Deploy with wrong API key
  - [ ] Verify: Data connector shows error
  - [ ] Verify: CCF logs show 401 errors

- [ ] **Test 7.2**: Missing endpoint
  - [ ] Stop Flask server
  - [ ] Wait for next poll
  - [ ] Verify: CCF retries 3 times
  - [ ] Verify: Logs show connection errors

- [ ] **Test 7.3**: Malformed JSON response
  - [ ] Modify Flask to return invalid JSON
  - [ ] Verify: CCF logs parsing error
  - [ ] Verify: No partial data ingested

- [ ] **Test 7.4**: 404 on nested call
  - [ ] Modify Step 1 to return non-existent asset name
  - [ ] Verify: CCF continues with other assets
  - [ ] Verify: Logs show 404 for specific asset

## 📊 Performance Testing

### ✅ Scale Tests

- [ ] **Test 8.1**: High volume test
  - [ ] Generate 100 vulnerabilities with 5 assets each
  - [ ] Expected: 1 + 100 + 500 = 601 API calls per poll
  - [ ] Verify: All data ingested successfully
  - [ ] Verify: Poll completes within 5 minutes

- [ ] **Test 8.2**: Rate limiting
  - [ ] Set `rateLimitQPS: 2` in PollerConfig
  - [ ] Verify: API calls are throttled
  - [ ] Verify: No 429 errors

- [ ] **Test 8.3**: Timeout handling
  - [ ] Add 30s sleep in Flask endpoint
  - [ ] Verify: CCF times out after 60s
  - [ ] Verify: Retry logic kicks in

## 📈 Metrics & Monitoring

### ✅ Operational Validation

- [ ] **Test 9.1**: CCF execution logs
  ```kql
  LAQueryLogs
  | where RequestTarget contains "cveBusterNestedAPI"
  | order by TimeGenerated desc
  | take 50
  ```

- [ ] **Test 9.2**: Data ingestion rate
  ```kql
  cveBusterNestedVulnerabilities_CL
  | summarize count() by bin(TimeGenerated, 5m)
  | order by TimeGenerated desc
  ```

- [ ] **Test 9.3**: Error rate
  ```kql
  LAQueryLogs
  | where RequestTarget contains "cveBusterNestedAPI"
  | summarize errors = countif(ResponseCode >= 400), total = count()
  | extend error_rate = (errors * 100.0) / total
  ```

## ✅ Final Sign-Off

- [ ] All pre-deployment tests passed
- [ ] All Azure deployment tests passed
- [ ] All data ingestion tests passed
- [ ] All feature validations passed
- [ ] All ISV patterns validated
- [ ] All error handling tests passed
- [ ] Performance acceptable for test scenario
- [ ] Documentation complete and accurate

---

**Testing Date**: _________________  
**Tested By**: _________________  
**Result**: ⬜ PASS ⬜ FAIL ⬜ PARTIAL  
**Notes**: _________________
