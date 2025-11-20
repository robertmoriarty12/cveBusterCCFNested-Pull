# 📚 cveBuster Nested API - Documentation Index

## 🚀 Quick Navigation

### Getting Started (5 minutes)
1. **[QUICKSTART.md](QUICKSTART.md)** - Step-by-step 5-minute setup guide
2. **[FINAL_SUMMARY.md](FINAL_SUMMARY.md)** - Complete solution overview and results

### Comprehensive Documentation
3. **[README.md](README.md)** - Full technical documentation with API flow diagrams
4. **[TESTING_CHECKLIST.md](TESTING_CHECKLIST.md)** - 50+ validation tests organized by category
5. **[COMPARISON.md](COMPARISON.md)** - Compare pagination vs nested API solutions

### Deployment
6. **[Deploy-Solution.ps1](Deploy-Solution.ps1)** - Automated deployment PowerShell script

### Additional Resources
7. **[SOLUTION_SUMMARY.md](SOLUTION_SUMMARY.md)** - High-level feature summary

---

## 📖 Documentation by Role

### For Testers
Start here to quickly validate the solution:
1. [QUICKSTART.md](QUICKSTART.md) - Set up in 5 minutes
2. [TESTING_CHECKLIST.md](TESTING_CHECKLIST.md) - Systematic validation (50+ tests)
3. Server/app_nested.py - Monitor API logs

**Key Commands:**
```powershell
# Generate data
python Server/generate_nested_data.py

# Start API
python Server/app_nested.py

# Test endpoints
$headers = @{ "Authorization" = "cvebuster-nested-key" }
Invoke-RestMethod -Uri "http://localhost:5000/api/stats" -Headers $headers
```

### For Developers
Understand the implementation details:
1. [README.md](README.md) - Architecture and API flow
2. [Data Connectors/cveBusterNestedAPI_ccf/cveBuster_PollerConfig.json](Data%20Connectors/cveBusterNestedAPI_ccf/cveBuster_PollerConfig.json) - CCF nested config
3. Server/app_nested.py - Mock API implementation
4. [COMPARISON.md](COMPARISON.md) - Compare with pagination pattern

**Key Files:**
- `cveBuster_PollerConfig.json` - ⭐ Most important (nested API config)
- `cveBuster_DCR.json` - Data transformation KQL
- `app_nested.py` - 3-level API implementation
- `generate_nested_data.py` - Test data generator

### For Product Managers
Understand feature coverage and ISV patterns:
1. [FINAL_SUMMARY.md](FINAL_SUMMARY.md) - Validation against PIF-2025-0019
2. [README.md](README.md) - ISV pattern mapping (section 🔍 Real-World ISV Patterns Tested)
3. [COMPARISON.md](COMPARISON.md) - Feature matrix and ISV recommendations

**Key Insights:**
- ✅ Validates all PIF-2025-0019 nested API requirements
- ✅ Covers 4 ISV patterns (CrowdStrike, TrendMicro, SecurityScorecard, BigID)
- ⚠️ Identifies 2 feature gaps with workarounds
- 📊 61 API calls per poll (1 + 15 + 45)

### For Solution Architects
Design and deployment guidance:
1. [README.md](README.md) - Full architecture diagrams
2. [COMPARISON.md](COMPARISON.md) - When to use nested API vs pagination
3. [Deploy-Solution.ps1](Deploy-Solution.ps1) - Automated deployment
4. Data/Solution_cveBuster.json - Solution packaging config

**Architecture Highlights:**
```
Step 0 (Root):    GET /api/vulnerabilities/ids
                  ↓ Extract IDs via KQL
Step 1 (Nested):  GET /api/vulnerabilities/{id} (×15)
                  ↓ Extract asset names via KQL
                  ↓ Join as "vulnerability"
Step 2 (Nested):  GET /api/assets/{name} (×45)
                  ↓ Join as "assets" array
Output:           Joined record with embedded vulnerability + assets[]
```

---

## 🎯 Quick Links by Task

### I want to...

#### Test the solution locally
→ [QUICKSTART.md](QUICKSTART.md) Steps 1-4

#### Deploy to Azure Sentinel
→ [QUICKSTART.md](QUICKSTART.md) Step 5 OR [Deploy-Solution.ps1](Deploy-Solution.ps1)

#### Understand nested API configuration
→ [README.md](README.md) Section: "2. CCF Configuration"  
→ [Data Connectors/cveBusterNestedAPI_ccf/cveBuster_PollerConfig.json](Data%20Connectors/cveBusterNestedAPI_ccf/cveBuster_PollerConfig.json)

#### Query ingested data
→ [QUICKSTART.md](QUICKSTART.md) Step 7  
→ [README.md](README.md) Section: "Step 6: Query Joined Data in Sentinel"

#### Validate all features
→ [TESTING_CHECKLIST.md](TESTING_CHECKLIST.md) - Complete checklist

#### Compare with pagination solution
→ [COMPARISON.md](COMPARISON.md)

#### Understand ISV patterns
→ [README.md](README.md) Section: "🔍 Real-World ISV Patterns Tested"  
→ [FINAL_SUMMARY.md](FINAL_SUMMARY.md) Section: "🏗️ ISV Pattern Coverage"

#### Troubleshoot issues
→ [QUICKSTART.md](QUICKSTART.md) Section: "🐛 Troubleshooting"

#### Extend to 4-5 levels
→ [README.md](README.md) Section: "🎓 Next Steps"

---

## 📁 File Structure Reference

```
cveBusterNestedAPI/
│
├── 📄 README.md                      (19KB) Full documentation
├── 📄 QUICKSTART.md                  (10KB) 5-minute setup
├── 📄 TESTING_CHECKLIST.md           (9KB)  50+ tests
├── 📄 COMPARISON.md                  (8KB)  Pagination vs Nested
├── 📄 FINAL_SUMMARY.md               (7KB)  Complete overview
├── 📄 SOLUTION_SUMMARY.md            (5KB)  Feature summary
├── 📄 INDEX.md                       (This file)
├── 📄 Deploy-Solution.ps1            Automated deployment
├── 📄 SolutionMetadata.json          Solution metadata
│
├── Server/
│   ├── 🐍 generate_nested_data.py   (5KB)  Data generator
│   ├── 🐍 app_nested.py              (10KB) Flask 3-level API
│   ├── 📄 requirements.txt            Python deps
│   └── 📄 .gitignore                  Ignore data files
│
├── Data Connectors/cveBusterNestedAPI_ccf/
│   ├── ⭐ cveBuster_PollerConfig.json       Nested API config (CRITICAL)
│   ├── 📄 cveBuster_connectorDefinition.json UI definition
│   ├── 📄 cveBuster_DCR.json                Data Collection Rule
│   └── 📄 cveBuster_Table.json              Table schema
│
├── Data/
│   └── 📄 Solution_cveBuster.json     Packaging config
│
└── Package/                          (Generated by createSolutionV3.ps1)
    ├── mainTemplate.json
    ├── createUiDefinition.json
    └── 3.0.0.zip
```

---

## 🔑 Key Concepts

### What is Nested API?
A CCF feature that allows chaining multiple API calls where:
- Step 0 returns IDs
- Step 1 uses those IDs to get details
- Step 2 uses data from Step 1 to get more enrichment
- All data is joined and sent as one record to Sentinel

### What is Data Joining?
Using `shouldJoinNestedData: true` to embed responses from nested steps into the parent record:
```json
{
  "vulnerability": {...from Step 1...},
  "assets": [{...from Step 2...}, {...}, ...]
}
```

### What is KQL Placeholder Parsing?
Using KQL to extract values from API responses and use them in next API call URLs:
```json
"stepPlaceholdersParsingKql": "source | project res = parse_json(data) | project ids = res['vulnerability_ids'] | mvexpand ids | project Url_PlaceHolder = ids"
```

This extracts vulnerability IDs and puts them into `$Url_PlaceHolder$` in the next API URL.

### What is Fan-Out Pattern?
When one API call returns multiple values, causing multiple next-level API calls:
```
Step 1: 1 call returns ["asset1", "asset2", "asset3"]
Step 2: 3 calls (one per asset)
```

---

## 📞 Getting Help

### Common Issues

**Q: No data in Sentinel after 10 minutes?**  
A: Check [QUICKSTART.md](QUICKSTART.md) → Troubleshooting section

**Q: How do I query nested data?**  
A: See [README.md](README.md) → "Step 6: Query Joined Data in Sentinel"

**Q: How many API calls should I expect?**  
A: See [FINAL_SUMMARY.md](FINAL_SUMMARY.md) → "📊 Expected Results"

**Q: When should I use nested API vs pagination?**  
A: See [COMPARISON.md](COMPARISON.md) → "Recommendation" section

### Testing Steps
1. Generate data: `python Server/generate_nested_data.py`
2. Start API: `python Server/app_nested.py`
3. Test endpoints manually (see QUICKSTART.md Step 3)
4. Package solution (see QUICKSTART.md Step 5)
5. Deploy to Sentinel (see QUICKSTART.md Step 5)
6. Wait 5-10 minutes for data
7. Query: `cveBusterNestedVulnerabilities_CL | take 10`

---

## 🎓 Learning Path

### Beginner (New to CCF)
1. Start with cveBusterSolutionPagination (simpler)
2. Read [COMPARISON.md](COMPARISON.md) to understand differences
3. Follow [QUICKSTART.md](QUICKSTART.md) to deploy this solution
4. Query data with sample KQL queries

### Intermediate (Familiar with CCF)
1. Read [README.md](README.md) - Focus on architecture diagrams
2. Study cveBuster_PollerConfig.json - Understand nested configuration
3. Run [TESTING_CHECKLIST.md](TESTING_CHECKLIST.md) tests
4. Modify to add 4th nested level

### Advanced (Building production connectors)
1. Read [README.md](README.md) - Focus on ISV pattern section
2. Study all CCF config files in detail
3. Review [FINAL_SUMMARY.md](FINAL_SUMMARY.md) for known gaps
4. Adapt pattern to your ISV's API structure

---

## 📊 Metrics & Results

After successful deployment:
- ✅ 61 API calls per 5-minute poll
- ✅ ~15 records ingested (recent vulnerabilities)
- ✅ ~3 assets per vulnerability (on average)
- ✅ 100% data join success rate
- ✅ 5-10 minutes to first data

---

## 🌟 Credits

**Built by**: Microsoft Security CxE ISV Team  
**Purpose**: Validate Sentinel CCF Nested API for ISV scenarios  
**Based on**: PIF-2025-0019 (Enable ISVs to retrieve data from nested APIs)  
**Version**: 3.0.0  
**Status**: Ready for Testing

---

**Start here**: [QUICKSTART.md](QUICKSTART.md) 🚀
