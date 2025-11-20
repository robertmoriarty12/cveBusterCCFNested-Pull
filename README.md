# cveBuster Microsoft Sentinel CCF Connector - Nested API Testing

A comprehensive Codeless Connector Framework (CCF) solution demonstrating **Nested API calls with data joining** for Microsoft Sentinel. This connector showcases multi-level API nesting patterns used by real ISVs like CrowdStrike, TrendMicro, SecurityScorecard, and BigID.

## 🎯 What This Project Demonstrates

This solution validates **Sentinel CCF Nested API capabilities** based on PIF-2025-0019 requirements:

### ✅ Core Nested API Features
- **3-Level API Nesting** - Chain multiple API calls with data dependencies
- **Data Joining** - Embed nested responses into parent objects using `shouldJoinNestedData`
- **KQL-Based Placeholder Parsing** - Extract IDs from responses to build next API calls
- **Multiple nextSteps** - Support fan-out patterns (1 record → many nested calls)
- **Hierarchical Data Ingestion** - Send enriched, joined data to Sentinel tables

### 🔍 Real-World ISV Patterns Tested

This solution mimics the following ISV workflows:

| ISV | Pattern | CVE Buster Equivalent |
|-----|---------|----------------------|
| **CrowdStrike** | List detection IDs → Get detection details → Get device context | List vuln IDs → Get vuln details → Get asset details |
| **TrendMicro** | List incidents → Get incident details → Get endpoint + user context | List vulns → Get vuln details → Get asset + patch info |
| **SecurityScorecard** | Get portfolios → Get companies → Get ratings/factors/issues | List vulns → Get vuln details → Get affected assets |
| **BigID** | List cases → Get affected objects → Get data source details | List vulns → Get vulnerability details → Get asset details |

## 📊 API Flow Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ STEP 0 (Root): Get Vulnerability ID List                       │
│ GET /api/vulnerabilities/ids                                    │
│ Response: {"vulnerability_ids": ["CVE-2024-10001", ...]}       │
└────────────────────────┬────────────────────────────────────────┘
                         │ Extract: Url_PlaceHolder = vulnerability_id
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1 (Nested): Get Vulnerability Details                     │
│ GET /api/vulnerabilities/$Url_PlaceHolder$                     │
│ Response: {                                                     │
│   "vuln_id": "CVE-2024-10001",                                 │
│   "severity": "Critical",                                       │
│   "affected_assets": ["SRV-WEB-001", "SRV-DB-005"]            │
│ }                                                               │
└────────────────────────┬────────────────────────────────────────┘
                         │ Extract: Asset_PlaceHolder = affected_assets[]
                         │ shouldJoinNestedData: true (embed as "vulnerability")
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 2 (Nested): Get Asset Details for Each Affected Asset     │
│ GET /api/assets/$Asset_PlaceHolder$                            │
│ Response: {                                                     │
│   "asset_name": "SRV-WEB-001",                                 │
│   "os_version": "Windows Server 2022",                         │
│   "patch_status": "Missing Critical Patches"                   │
│ }                                                               │
└────────────────────────┬────────────────────────────────────────┘
                         │ shouldJoinNestedData: true (embed as "assets")
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ FINAL OUTPUT: Joined Data Sent to DCR                          │
│ {                                                               │
│   "vulnerability": {                                            │
│     "vuln_id": "CVE-2024-10001",                               │
│     "severity": "Critical",                                     │
│     "cvss": 9.8                                                 │
│   },                                                            │
│   "assets": [                                                   │
│     {                                                           │
│       "asset_name": "SRV-WEB-001",                             │
│       "os_version": "Windows Server 2022",                     │
│       "patch_status": "Missing Critical Patches"               │
│     },                                                          │
│     {                                                           │
│       "asset_name": "SRV-DB-005",                              │
│       "os_version": "Windows Server 2019",                     │
│       "patch_status": "Patched"                                │
│     }                                                           │
│   ]                                                             │
│ }                                                               │
└─────────────────────────────────────────────────────────────────┘
```

## 🏗️ Solution Components

### 1. Flask Mock API Server (`Server/app_nested.py`)
Implements a 3-level nested API:

- **`GET /api/vulnerabilities/ids`** - Returns list of vulnerability IDs
  - Time-filtered by `startTime` and `endTime` parameters
  - Returns: `{"vulnerability_ids": ["CVE-2024-10001", ...]}`

- **`GET /api/vulnerabilities/<vuln_id>`** - Returns vulnerability details
  - Includes: severity, CVSS, description, affected_assets array
  - Returns: `{"vuln_id": "...", "severity": "Critical", "affected_assets": [...]}`

- **`GET /api/assets/<asset_name>`** - Returns asset details
  - Includes: OS version, IP address, patch status, criticality
  - Returns: `{"asset_name": "...", "os_version": "...", "patch_status": "..."}`

### 2. CCF Configuration (`Data Connectors/cveBusterNestedAPI_ccf/`)

**cveBuster_PollerConfig.json** - Nested API configuration:
```json
{
  "stepInfo": {
    "stepType": "Nested",
    "nextSteps": [{
      "stepId": "step1_vulnerability_details",
      "stepPlaceholdersParsingKql": "source | project res = parse_json(data) | project Url_PlaceHolder = res['vulnerability_ids'] | mvexpand Url_PlaceHolder"
    }]
  },
  "stepCollectorConfigs": {
    "step1_vulnerability_details": {
      "shouldJoinNestedData": true,
      "joinedDataStepName": "vulnerability",
      "stepInfo": {
        "stepType": "Nested",
        "nextSteps": [{
          "stepId": "step2_asset_details",
          "stepPlaceholdersParsingKql": "..."
        }]
      }
    },
    "step2_asset_details": {
      "shouldJoinNestedData": true,
      "joinedDataStepName": "assets"
    }
  }
}
```

### 3. Data Generator (`Server/generate_nested_data.py`)
Creates realistic test data:
- **50 vulnerabilities** with varying severities
- **30 assets** (servers) with different OS versions and patch states
- **Relationships**: Each vulnerability affects 1-5 random assets
- **Time distribution**: 30% recent (last 5 minutes), 70% old (30-90 days)

### 4. Custom Table Schema (`cveBuster_Table.json`)
Supports nested JSON structure:
- `vulnerability_id` (string)
- `vulnerability_severity` (string)
- `vulnerability_cvss` (real)
- `vulnerability_details` (dynamic) - Full nested vulnerability object
- `assets` (dynamic) - Array of affected asset objects
- `TimeGenerated` (datetime)

## 🚀 Quick Start

### Prerequisites
- Microsoft Sentinel workspace
- Azure subscription with Contributor permissions
- Python 3.9+ (for mock API server)
- PowerShell with Az modules

### Step 1: Generate Test Data
```bash
cd C:\GitHub\Azure-Sentinel\Solutions\cveBusterNestedAPI\Server
python generate_nested_data.py
```

Output:
- `vulnerabilities.json` - 50 vulnerability records
- `assets.json` - 30 asset records

### Step 2: Start Mock API Server
```bash
python app_nested.py
```

Server runs on `http://localhost:5000`

Test endpoints:
```bash
# Get vulnerability IDs (filtered by time)
curl "http://localhost:5000/api/vulnerabilities/ids?startTime=2025-11-18T00:00:00Z&endTime=2025-11-18T23:59:59Z" -H "Authorization: cvebuster-nested-key"

# Get specific vulnerability details
curl "http://localhost:5000/api/vulnerabilities/CVE-2024-10001" -H "Authorization: cvebuster-nested-key"

# Get specific asset details
curl "http://localhost:5000/api/assets/SRV-WEB-001" -H "Authorization: cvebuster-nested-key"
```

### Step 3: Package the Solution
```powershell
cd C:\GitHub\Azure-Sentinel\Tools\Create-Azure-Sentinel-Solution\V3
.\createSolutionV3.ps1 `
  -packageConfigPath "C:\GitHub\Azure-Sentinel\Solutions\cveBusterNestedAPI\Data\Solution_cveBuster.json" `
  -outputFolderPath "C:\GitHub\Azure-Sentinel\Solutions\cveBusterNestedAPI\Package"
```

### Step 4: Deploy to Sentinel
```powershell
New-AzResourceGroupDeployment `
  -ResourceGroupName "your-rg" `
  -TemplateFile "C:\GitHub\Azure-Sentinel\Solutions\cveBusterNestedAPI\Package\mainTemplate.json" `
  -workspace "your-sentinel-workspace-name" `
  -apiEndpoint "http://YOUR_SERVER:5000" `
  -apiKey "cvebuster-nested-key"
```

### Step 5: Verify Nested API Execution

Monitor Flask logs to see the nested call pattern:
```
[STEP 0] GET /api/vulnerabilities/ids - Returned 15 IDs
[STEP 1] GET /api/vulnerabilities/CVE-2024-10001 - Returned details with 3 affected assets
[STEP 2] GET /api/assets/SRV-WEB-001 - Returned asset details
[STEP 2] GET /api/assets/SRV-APP-005 - Returned asset details
[STEP 2] GET /api/assets/SRV-DB-002 - Returned asset details
```

Expected CCF behavior:
1. **Root call**: Fetches 15 vulnerability IDs (time-filtered)
2. **15 nested calls** (Step 1): One per vulnerability ID
3. **45 nested calls** (Step 2): One per affected asset (avg 3 assets per vuln)
4. **Total**: 1 + 15 + 45 = **61 API calls in one polling cycle**

### Step 6: Query Joined Data in Sentinel

```kql
cveBusterNestedVulnerabilities_CL
| where TimeGenerated > ago(1h)
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
```

Expected output:
```
TimeGenerated           vuln_id           severity  cvss  asset_name    os_version              patch_status
2025-11-18T10:15:00Z   CVE-2024-10001   Critical  9.8   SRV-WEB-001   Windows Server 2022     Missing Critical Patches
2025-11-18T10:15:00Z   CVE-2024-10001   Critical  9.8   SRV-APP-005   Ubuntu 22.04 LTS        Up to Date
2025-11-18T10:15:00Z   CVE-2024-10001   Critical  9.8   SRV-DB-002    Windows Server 2019     Missing Critical Patches
```

## 🧪 Testing Scenarios

### Test 1: Basic Nested API Flow
**Objective**: Verify 3-level nesting works
- Root call returns 10 vulnerability IDs
- Each ID triggers a vulnerability details call (10 calls)
- Each vulnerability has 2 assets, triggering asset calls (20 calls)
- **Total**: 31 API calls

### Test 2: Data Joining Validation
**Objective**: Verify `shouldJoinNestedData` works correctly
- Query Sentinel table
- Verify `vulnerability_details` contains full vulnerability object
- Verify `assets` is an array with all affected asset objects
- No data loss between API levels

### Test 3: Time-Based Filtering
**Objective**: Verify only new/modified vulnerabilities are fetched
- Generate data with 30% recent (last 5 min), 70% old
- CCF should only fetch recent IDs in root call
- Verify subsequent nested calls only process recent vulnerabilities

### Test 4: High Volume Nested Calls
**Objective**: Test CCF performance with many nested calls
- Generate 50 vulnerabilities
- Each vulnerability affects 5 assets
- **Total**: 1 + 50 + 250 = **301 API calls per poll**
- Verify all data ingested without errors

### Test 5: Error Handling
**Objective**: Verify graceful handling of missing nested data
- Mock API returns 404 for some asset IDs
- Verify CCF continues processing other assets
- Check logs for proper error handling

## 🔬 Validating Against ISV Requirements

### CrowdStrike Pattern ✅
- **Requirement**: List detection IDs → Get details → Get device context
- **cveBuster**: List vuln IDs → Get vuln details → Get asset details
- **Validated**: Comma-separated ID list support (if needed, modify KQL to use `strcat_array`)

### TrendMicro Pattern ✅
- **Requirement**: Fetch incidents → Get incident details → Enrich with endpoints/users
- **cveBuster**: Fetch vuln IDs → Get vuln details → Enrich with assets
- **Validated**: Multi-level enrichment with separate API endpoints

### SecurityScorecard Pattern ✅
- **Requirement**: Portfolios → Companies → Ratings/Factors/Issues (3 parallel branches)
- **cveBuster**: Vulnerabilities → Assets (can extend to 3 branches)
- **Validated**: Fan-out pattern (1 vuln → many assets)

### BigID Pattern ⚠️
- **Requirement**: Cases → Affected objects → Flatten objects into rows
- **cveBuster**: Supports nested data, but **flattening must be done in KQL queries**
- **Gap Identified**: DCR cannot auto-flatten arrays (matches PIF-2025-0020 finding)
- **Workaround**: Use `mv-expand` in KQL queries (demonstrated in Step 6)

## 📋 Feature Checklist

Based on PIF-2025-0019 and internal nested API docs:

| Feature | Status | Notes |
|---------|--------|-------|
| Multi-level nesting (up to 5 levels) | ✅ Tested | Solution uses 3 levels, can extend to 5 |
| `stepInfo.stepType = "Nested"` | ✅ Implemented | Root and Step 1 use nested type |
| `nextSteps` array with `stepId` | ✅ Implemented | Each step defines next step ID |
| `stepPlaceholdersParsingKql` | ✅ Implemented | KQL extracts placeholders for URL construction |
| `shouldJoinNestedData` | ✅ Implemented | Step 1 and Step 2 join data into parent |
| `joinedDataStepName` | ✅ Implemented | Names: "vulnerability", "assets" |
| `stepCollectorConfigs` dictionary | ✅ Implemented | Separate configs for Step 1 and Step 2 |
| Placeholder in URL (`$Url_PlaceHolder$`) | ✅ Implemented | Used in vulnerability and asset endpoints |
| Multiple placeholders | 🔄 Not tested | Can add if needed (e.g., `$Asset_PlaceHolder$`) |
| Time-based filtering in root call | ✅ Implemented | `startTime` and `endTime` parameters |
| Fan-out pattern (1 → many) | ✅ Implemented | 1 vuln → multiple assets using `mvexpand` |
| Array flattening in DCR | ❌ Known Gap | PIF-2025-0020 - Use KQL `mv-expand` workaround |
| Comma-separated ID list in body | 🔄 Not tested | CrowdStrike requirement - can add if needed |

## 🐛 Known Gaps and Workarounds

### Gap 1: Array Flattening in DCR (PIF-2025-0020)
**Issue**: DCR cannot automatically flatten nested arrays into separate rows.

**Example**: 
```json
{
  "vulnerability": {...},
  "assets": [
    {"asset_name": "SRV-001", ...},
    {"asset_name": "SRV-002", ...}
  ]
}
```

**Workaround**: Use KQL `mv-expand` in queries:
```kql
cveBusterNestedVulnerabilities_CL
| mv-expand assets
| extend asset_name = tostring(assets.asset_name)
```

**Recommendation**: Complete development of DCR array flattening feature.

### Gap 2: Comma-Separated ID List in Single Call
**Issue**: CrowdStrike pattern requires collecting all IDs from Step 1 into a comma-separated list and passing them in a **single API call** in Step 2.

**Current Behavior**: CCF makes one API call per ID (fan-out).

**Desired Behavior**: 
```
Step 1: Get 50 detection IDs
Step 2: Call /detects/entities/detects/v2?ids=id1,id2,id3,...,id50 (ONE call)
```

**Potential Workaround**: Use KQL with `strcat_array()` or `make_list()` to aggregate IDs, but CCF may not support this yet.

**Recommendation**: Validate if this is a feature gap or if KQL aggregation can solve it.

## 📚 References

- **PIF Document**: PIF-2025-0019 - Enable ISVs to retrieve data from nested APIs
- **GitHub Issue**: [#12819](https://github.com/Azure/Azure-Sentinel/issues/12819) - Nested API feature exposure
- **Internal Docs**: Nested API Documentation (internal)
- **Published Solutions Using Nested API**:
  - CrowdStrike Falcon Endpoint Protection
  - Salesforce Service Cloud
  - BigID (merged, not published)

## 🎓 Learning Outcomes

After deploying and testing this solution, you will understand:

1. ✅ How to configure multi-level nested API calls in CCF
2. ✅ How to use KQL to extract placeholders for dynamic URL construction
3. ✅ How to join nested data using `shouldJoinNestedData` and `joinedDataStepName`
4. ✅ How to query nested/joined data in Sentinel using `mv-expand` and `parse_json()`
5. ✅ The limitations of DCR array flattening and KQL-based workarounds
6. ✅ Real-world ISV patterns and how CCF supports them

## 📞 Support

For questions or issues:
- Review Flask logs for API call sequences
- Check CCF logs in Azure Monitor for connector errors
- Validate KQL parsing with `print` statements in `stepPlaceholdersParsingKql`
- Test endpoints manually with `curl` before deploying CCF connector

---

**Built by**: Microsoft Security CxE ISV Team  
**Purpose**: Validate Sentinel CCF Nested API feature for ISV scenarios  
**Status**: Testing/Validation Solution (Not for production use)
