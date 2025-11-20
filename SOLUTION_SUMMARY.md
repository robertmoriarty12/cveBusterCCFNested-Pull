# cveBuster Nested API Testing Solution

## ✅ Solution Complete!

This is a comprehensive **Sentinel CCF Nested API testing solution** based on PIF-2025-0019 requirements.

### 📁 What Was Created

```
cveBusterNestedAPI/
├── README.md                           # Complete solution documentation
├── QUICKSTART.md                       # 5-minute quick start guide
├── SolutionMetadata.json              # Solution package metadata
│
├── Server/                            # Mock API Server
│   ├── generate_nested_data.py       # Data generator (50 vulns, 30 assets)
│   └── app_nested.py                 # Flask 3-level nested API server
│
├── Data Connectors/cveBusterNestedAPI_ccf/
│   ├── cveBuster_PollerConfig.json   # CCF nested config (critical!)
│   ├── cveBuster_connectorDefinition.json
│   ├── cveBuster_DCR.json            # Data Collection Rule with KQL transform
│   └── cveBuster_Table.json          # Custom table schema
│
├── Data/
│   └── Solution_cveBuster.json       # Solution packaging config
│
└── Package/                          # (Created by createSolutionV3.ps1)
    ├── mainTemplate.json
    ├── createUiDefinition.json
    └── 3.0.0.zip
```

### 🎯 What This Tests

| Feature | Status | ISV Pattern |
|---------|--------|-------------|
| 3-level nested API | ✅ Implemented | CrowdStrike, TrendMicro |
| Data joining (`shouldJoinNestedData`) | ✅ Implemented | All ISVs |
| KQL placeholder extraction | ✅ Implemented | All ISVs |
| Fan-out pattern (1 → many) | ✅ Implemented | SecurityScorecard, BigID |
| Time-based filtering | ✅ Implemented | All ISVs |
| `stepCollectorConfigs` | ✅ Implemented | Core feature |
| Dynamic schema (nested JSON) | ✅ Implemented | BigID pattern |

### 🚀 Quick Start

1. **Generate data**: `python Server/generate_nested_data.py`
2. **Start API**: `python Server/app_nested.py`
3. **Test manually**: See QUICKSTART.md Step 3
4. **Package**: Use createSolutionV3.ps1
5. **Deploy**: Upload to Sentinel
6. **Query**: See QUICKSTART.md Step 7

### 📊 Expected API Flow

```
Poll Cycle (every 5 minutes):

Step 0: GET /api/vulnerabilities/ids
        ↓ Returns 15 IDs (recent)
        
Step 1: GET /api/vulnerabilities/CVE-2024-10001  ┐
        GET /api/vulnerabilities/CVE-2024-10002  │ 15 calls
        ...                                      │ (parallel)
        GET /api/vulnerabilities/CVE-2024-10015  ┘
        ↓ Each returns 3 affected assets
        
Step 2: GET /api/assets/SRV-WEB-001  ┐
        GET /api/assets/SRV-APP-005  │ ~45 calls
        ...                          │ (parallel, fan-out)
        GET /api/assets/SRV-DB-030   ┘

Total: 1 + 15 + 45 = 61 API calls per poll
```

### 🔍 Key Configuration Highlights

**cveBuster_PollerConfig.json**:
```json
{
  "stepInfo": {
    "stepType": "Nested",
    "nextSteps": [{
      "stepId": "step1_vulnerability_details",
      "stepPlaceholdersParsingKql": "source | project res = parse_json(data) | project ids = res['vulnerability_ids'] | mvexpand ids | project Url_PlaceHolder = ids"
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
          "stepPlaceholdersParsingKql": "source | project res = parse_json(data) | project assets = res['affected_assets'] | mvexpand assets | project Asset_PlaceHolder = assets"
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

### 🧪 Validation Queries

```kql
// View joined data with mv-expand
cveBusterNestedVulnerabilities_CL
| extend vuln = parse_json(vulnerability_details)
| extend vuln_id = tostring(vuln.vuln_id)
| extend severity = tostring(vuln.severity)
| extend affected_assets = parse_json(assets)
| mv-expand affected_assets
| extend asset_name = tostring(affected_assets.asset_name)
| extend patch_status = tostring(affected_assets.patch_status)
| project TimeGenerated, vuln_id, severity, asset_name, patch_status
```

### 🎓 What You'll Learn

1. How to configure multi-level nested API calls in CCF
2. How to use KQL to extract placeholders for dynamic URLs
3. How to join nested data using `shouldJoinNestedData`
4. How to handle fan-out patterns (1 → many nested calls)
5. How to query nested/joined data with `mv-expand`
6. Real ISV patterns and CCF capabilities

### 📋 Known Gaps Identified

1. **Array Flattening in DCR** (PIF-2025-0020)
   - DCR cannot auto-flatten nested arrays
   - **Workaround**: Use `mv-expand` in KQL queries

2. **Comma-Separated ID Lists** (CrowdStrike pattern)
   - Need to aggregate IDs into single API call
   - **Status**: Untested, may need new CCF feature

### 📞 Support

- **Full Documentation**: README.md
- **Quick Start**: QUICKSTART.md  
- **API Testing**: Test with `curl` or PowerShell
- **CCF Logs**: Check Azure Monitor → LAQueryLogs

### ✨ Built By

**Microsoft Security CxE ISV Team**  
Purpose: Validate Sentinel CCF Nested API feature for ISV scenarios  
Status: Testing/Validation Solution

---

**Ready to test?** → See `QUICKSTART.md` for 5-minute setup!
