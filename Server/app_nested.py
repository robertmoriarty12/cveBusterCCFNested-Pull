from flask import Flask, request, jsonify
import json
from datetime import datetime

app = Flask(__name__)

# API Key for authentication
API_KEY = "cvebuster-nested-key"

# Load data on startup
vulnerabilities = []
assets = {}

def load_data():
    """Load vulnerability and asset data from JSON files."""
    global vulnerabilities, assets
    
    try:
        with open('vulnerabilities.json', 'r') as f:
            vulnerabilities = json.load(f)
        print(f"✅ Loaded {len(vulnerabilities)} vulnerabilities")
    except FileNotFoundError:
        print("❌ vulnerabilities.json not found. Run generate_nested_data.py first!")
        vulnerabilities = []
    
    try:
        with open('assets.json', 'r') as f:
            assets_list = json.load(f)
            # Convert to dict for fast lookup
            assets = {a["asset_name"]: a for a in assets_list}
        print(f"✅ Loaded {len(assets)} assets")
    except FileNotFoundError:
        print("❌ assets.json not found. Run generate_nested_data.py first!")
        assets = {}

def check_auth():
    """Verify API key authorization."""
    auth_header = request.headers.get('Authorization', '')
    if auth_header != API_KEY:
        return False
    return True

def parse_iso_datetime(dt_str):
    """Parse ISO 8601 datetime string to datetime object."""
    try:
        if dt_str.endswith('Z'):
            dt_str = dt_str[:-1] + '+00:00'
        return datetime.fromisoformat(dt_str)
    except Exception as e:
        print(f"⚠️  Error parsing datetime '{dt_str}': {e}")
        return None

def filter_by_time_range(vulns, start_time_str=None, end_time_str=None):
    """Filter vulnerabilities by LastModified time range."""
    if not start_time_str and not end_time_str:
        return vulns
    
    start_time = parse_iso_datetime(start_time_str) if start_time_str else None
    end_time = parse_iso_datetime(end_time_str) if end_time_str else None
    
    filtered = []
    for vuln in vulns:
        last_modified = parse_iso_datetime(vuln.get('last_modified', ''))
        if last_modified is None:
            continue
        
        # Check if within time range (exclusive on both ends for CCF compatibility)
        if start_time and last_modified <= start_time:
            continue
        if end_time and last_modified >= end_time:
            continue
        
        filtered.append(vuln)
    
    return filtered

@app.route('/')
def home():
    """Health check endpoint."""
    return jsonify({
        "service": "cveBuster Nested API Server",
        "status": "running",
        "vulnerabilities_loaded": len(vulnerabilities),
        "assets_loaded": len(assets),
        "endpoints": {
            "step_0_get_ids": "GET /api/vulnerabilities/ids?startTime=<iso8601>&endTime=<iso8601>",
            "step_1_get_vuln_details": "GET /api/vulnerabilities/<vuln_id>",
            "step_2_get_asset_details": "GET /api/assets/<asset_name>"
        }
    })

# ============================================================================
# STEP 0: Get Vulnerability IDs (Root Call)
# ============================================================================
@app.route('/api/vulnerabilities/ids', methods=['GET'])
def get_vulnerability_ids():
    """
    STEP 0: Get list of vulnerability IDs (root call for nested API).
    
    Supports time filtering via startTime and endTime parameters.
    This mimics the CrowdStrike, TrendMicro, SecurityScorecard pattern
    where the first call returns a list of IDs.
    
    Query Parameters:
    - startTime: ISO 8601 datetime (e.g., 2025-11-18T00:00:00Z)
    - endTime: ISO 8601 datetime (e.g., 2025-11-18T23:59:59Z)
    
    Returns:
    {
      "vulnerability_ids": ["CVE-2024-10001", "CVE-2024-10002", ...],
      "count": 15,
      "time_range": {
        "start": "2025-11-18T00:00:00Z",
        "end": "2025-11-18T23:59:59Z"
      }
    }
    """
    if not check_auth():
        return jsonify({"error": "Unauthorized"}), 401
    
    # Get time filter parameters
    start_time = request.args.get('startTime')
    end_time = request.args.get('endTime')
    
    # Filter vulnerabilities by time
    filtered_vulns = filter_by_time_range(vulnerabilities, start_time, end_time)
    
    # Extract just the IDs
    vuln_ids = [v["vuln_id"] for v in filtered_vulns]
    
    # Log request
    print(f"[STEP 0] GET /api/vulnerabilities/ids")
    print(f"         TimeFilter: {start_time} to {end_time}")
    print(f"         Returned {len(vuln_ids)} IDs")
    
    response = {
        "vulnerability_ids": vuln_ids,
        "count": len(vuln_ids),
        "time_range": {
            "start": start_time,
            "end": end_time
        }
    }
    
    return jsonify(response)

# ============================================================================
# STEP 1: Get Vulnerability Details
# ============================================================================
@app.route('/api/vulnerabilities/<vuln_id>', methods=['GET'])
def get_vulnerability_details(vuln_id):
    """
    STEP 1: Get detailed information about a specific vulnerability.
    
    This is called by CCF using the $Url_PlaceHolder$ extracted from Step 0.
    Returns full vulnerability details including affected_assets array.
    
    Path Parameter:
    - vuln_id: CVE identifier (e.g., CVE-2024-10001)
    
    Returns:
    {
      "vuln_id": "CVE-2024-10001",
      "vuln_title": "Remote Code Execution in Apache",
      "severity": "Critical",
      "cvss": 9.8,
      "vuln_type": "Remote Code Execution",
      "description": "...",
      "affected_assets": ["SRV-WEB-001", "SRV-APP-005"],
      "patch_available": true,
      "exploit_available": true,
      "exploit_public": false,
      "discovery_date": "2025-10-01T00:00:00Z",
      "last_modified": "2025-11-18T10:00:00Z",
      "status": "Open",
      "cve_url": "https://nvd.nist.gov/vuln/detail/CVE-2024-10001"
    }
    """
    if not check_auth():
        return jsonify({"error": "Unauthorized"}), 401
    
    # Find vulnerability
    vuln = next((v for v in vulnerabilities if v["vuln_id"] == vuln_id), None)
    
    if not vuln:
        print(f"[STEP 1] GET /api/vulnerabilities/{vuln_id} - NOT FOUND")
        return jsonify({"error": "Vulnerability not found"}), 404
    
    # Log request
    print(f"[STEP 1] GET /api/vulnerabilities/{vuln_id}")
    print(f"         Severity: {vuln['severity']}, Affected Assets: {len(vuln['affected_assets'])}")
    
    return jsonify(vuln)

# ============================================================================
# STEP 2: Get Asset Details
# ============================================================================
@app.route('/api/assets/<asset_name>', methods=['GET'])
def get_asset_details(asset_name):
    """
    STEP 2: Get detailed information about a specific asset (server).
    
    This is called by CCF using the $Asset_PlaceHolder$ extracted from Step 1's
    affected_assets array. This mimics the CrowdStrike/TrendMicro pattern of
    enriching detections with device/endpoint context.
    
    Path Parameter:
    - asset_name: Server name (e.g., SRV-WEB-001)
    
    Returns:
    {
      "asset_name": "SRV-WEB-001",
      "asset_type": "WEB",
      "os_version": "Windows Server 2022",
      "ip_address": "10.10.5.42",
      "criticality": "High",
      "patch_status": "Missing Critical Patches",
      "last_seen": "2025-11-18T08:00:00Z",
      "owner": "Team-Infrastructure",
      "location": "US-East"
    }
    """
    if not check_auth():
        return jsonify({"error": "Unauthorized"}), 401
    
    # Find asset
    asset = assets.get(asset_name)
    
    if not asset:
        print(f"[STEP 2] GET /api/assets/{asset_name} - NOT FOUND")
        return jsonify({"error": "Asset not found"}), 404
    
    # Log request
    print(f"[STEP 2] GET /api/assets/{asset_name}")
    print(f"         OS: {asset['os_version']}, Patch Status: {asset['patch_status']}")
    
    return jsonify(asset)

# ============================================================================
# Health Check and Stats
# ============================================================================
@app.route('/api/stats', methods=['GET'])
def get_stats():
    """
    Get statistics about the test data.
    Useful for understanding the expected API call volume.
    """
    if not check_auth():
        return jsonify({"error": "Unauthorized"}), 401
    
    # Count recent vulnerabilities (last 5 minutes)
    now = datetime.utcnow()
    recent_vulns = [v for v in vulnerabilities 
                    if (now - parse_iso_datetime(v['last_modified'])).total_seconds() < 300]
    
    # Calculate total relationships
    total_relationships = sum(len(v['affected_assets']) for v in vulnerabilities)
    recent_relationships = sum(len(v['affected_assets']) for v in recent_vulns)
    
    stats = {
        "total_vulnerabilities": len(vulnerabilities),
        "recent_vulnerabilities": len(recent_vulns),
        "total_assets": len(assets),
        "total_vuln_asset_relationships": total_relationships,
        "recent_vuln_asset_relationships": recent_relationships,
        "expected_api_calls_per_poll": {
            "step_0_get_ids": 1,
            "step_1_vuln_details": len(recent_vulns),
            "step_2_asset_details": recent_relationships,
            "total": 1 + len(recent_vulns) + recent_relationships
        },
        "severity_distribution": {
            "Critical": sum(1 for v in vulnerabilities if v['severity'] == 'Critical'),
            "High": sum(1 for v in vulnerabilities if v['severity'] == 'High'),
            "Medium": sum(1 for v in vulnerabilities if v['severity'] == 'Medium'),
            "Low": sum(1 for v in vulnerabilities if v['severity'] == 'Low')
        }
    }
    
    return jsonify(stats)

if __name__ == '__main__':
    print("=" * 70)
    print("🚀 cveBuster Nested API Server")
    print("=" * 70)
    
    # Load data
    load_data()
    
    if not vulnerabilities or not assets:
        print("\n⚠️  WARNING: Data files not loaded!")
        print("   Run: python generate_nested_data.py")
        print()
    
    print("\n📡 API Endpoints:")
    print("   Step 0: GET /api/vulnerabilities/ids?startTime=<iso>&endTime=<iso>")
    print("   Step 1: GET /api/vulnerabilities/<vuln_id>")
    print("   Step 2: GET /api/assets/<asset_name>")
    print("   Stats:  GET /api/stats")
    
    print("\n🔑 Authentication:")
    print(f"   Header: Authorization: {API_KEY}")
    
    print("\n🧪 Test Commands:")
    print(f"   curl 'http://localhost:5000/api/vulnerabilities/ids' -H 'Authorization: {API_KEY}'")
    print(f"   curl 'http://localhost:5000/api/vulnerabilities/CVE-2024-10001' -H 'Authorization: {API_KEY}'")
    print(f"   curl 'http://localhost:5000/api/assets/SRV-WEB-001' -H 'Authorization: {API_KEY}'")
    print(f"   curl 'http://localhost:5000/api/stats' -H 'Authorization: {API_KEY}'")
    
    print("\n" + "=" * 70)
    print("🟢 Server starting on http://0.0.0.0:5000")
    print("=" * 70 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
