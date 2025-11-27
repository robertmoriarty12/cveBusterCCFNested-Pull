import json
import random
from datetime import datetime, timedelta

def generate_assets(num_assets=30):
    """Generate mock asset (server) data."""
    os_versions = [
        "Windows Server 2022",
        "Windows Server 2019", 
        "Windows Server 2016",
        "Ubuntu 22.04 LTS",
        "Ubuntu 20.04 LTS",
        "Red Hat Enterprise Linux 8",
        "Red Hat Enterprise Linux 9"
    ]
    
    patch_statuses = [
        "Up to Date",
        "Missing Critical Patches",
        "Missing Important Patches", 
        "Missing Optional Patches",
        "Patch Pending Reboot"
    ]
    
    asset_types = ["WEB", "APP", "DB", "DC", "FILE", "MAIL"]
    criticalities = ["Critical", "High", "Medium", "Low"]
    
    assets = []
    for i in range(1, num_assets + 1):
        asset_type = random.choice(asset_types)
        asset = {
            "asset_name": f"SRV-{asset_type}-{i:03d}",
            "asset_type": asset_type,
            "os_version": random.choice(os_versions),
            "ip_address": f"10.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}",
            "criticality": random.choice(criticalities),
            "patch_status": random.choice(patch_statuses),
            "last_seen": (datetime.utcnow() - timedelta(hours=random.randint(0, 48))).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "owner": f"Team-{random.choice(['Security', 'Infrastructure', 'Application', 'Database'])}",
            "location": random.choice(["US-East", "US-West", "EU-West", "APAC-Southeast"])
        }
        assets.append(asset)
    
    return assets

def generate_vulnerabilities(assets, num_vulns=50):
    """
    Generate mock vulnerability data with asset relationships.
    
    Time distribution:
    - 30% recent (last 5 minutes) - for CCF testing
    - 70% old (30-90 days ago)
    """
    severities = ["Critical", "High", "Medium", "Low"]
    vuln_types = [
        "Remote Code Execution",
        "Privilege Escalation",
        "Information Disclosure",
        "Denial of Service",
        "SQL Injection",
        "Cross-Site Scripting",
        "Buffer Overflow"
    ]
    
    now = datetime.utcnow()
    vulnerabilities = []
    
    for i in range(1, num_vulns + 1):
        # 30% recent (last 5 minutes), 70% old (30-90 days)
        if random.random() < 0.30:
            # Recent records - within last 5 minutes (300 seconds)
            seconds_ago = random.randint(0, 300)
            last_modified = now - timedelta(seconds=seconds_ago)
        else:
            # Old records - 30 to 90 days ago
            days_ago = random.randint(30, 90)
            last_modified = now - timedelta(days=days_ago)
        
        # Discovery date is before last modified
        days_before = random.randint(1, 30)
        discovery_date = last_modified - timedelta(days=days_before)
        
        severity = random.choice(severities)
        
        # CVSS score aligned with severity
        if severity == "Critical":
            cvss = round(random.uniform(9.0, 10.0), 1)
        elif severity == "High":
            cvss = round(random.uniform(7.0, 8.9), 1)
        elif severity == "Medium":
            cvss = round(random.uniform(4.0, 6.9), 1)
        else:
            cvss = round(random.uniform(0.1, 3.9), 1)
        
        # Each vulnerability affects 1-5 random assets
        num_affected = random.randint(1, 5)
        affected_assets = random.sample([a["asset_name"] for a in assets], num_affected)
        
        vuln = {
            "vuln_id": f"CVE-2024-{10000 + i}",
            "vuln_title": f"{random.choice(vuln_types)} in {random.choice(['Apache', 'Nginx', 'IIS', 'MySQL', 'PostgreSQL', 'Redis', 'Tomcat'])}",
            "severity": severity,
            "cvss": cvss,
            "vuln_type": random.choice(vuln_types),
            "description": f"A {severity.lower()} severity vulnerability allowing {random.choice(vuln_types).lower()}",
            "affected_assets": affected_assets,
            "patch_available": random.choice([True, False]),
            "exploit_available": random.choice([True, False]),
            "exploit_public": random.choice([True, False]),
            "discovery_date": discovery_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "last_modified": last_modified.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "status": random.choice(["Open", "In Progress", "Patched", "Mitigated", "Risk Accepted"]),
            "cve_url": f"https://nvd.nist.gov/vuln/detail/CVE-2024-{10000 + i}"
        }
        vulnerabilities.append(vuln)
    
    return vulnerabilities

if __name__ == "__main__":
    print("Generating nested API test data...")
    print("=" * 60)
    
    # Generate assets first
    print("\n1. Generating 30 asset records...")
    assets = generate_assets(30)
    
    with open('assets.json', 'w') as f:
        json.dump(assets, f, indent=2)
    print(f"   ✅ Created assets.json with {len(assets)} assets")
    
    # Generate vulnerabilities with asset relationships
    print("\n2. Generating 50 vulnerability records...")
    vulns = generate_vulnerabilities(assets, 50)
    
    with open('vulnerabilities.json', 'w') as f:
        json.dump(vulns, f, indent=2)
    
    # Count recent vs old
    now = datetime.utcnow()
    recent_count = sum(1 for v in vulns 
                      if (now - datetime.strptime(v['last_modified'], "%Y-%m-%dT%H:%M:%SZ")).total_seconds() < 300)
    
    print(f"   ✅ Created vulnerabilities.json with {len(vulns)} vulnerabilities")
    print(f"      - Recent (last 5 min): {recent_count}")
    print(f"      - Old (30-90 days): {len(vulns) - recent_count}")
    
    # Calculate total affected asset relationships
    total_relationships = sum(len(v['affected_assets']) for v in vulns)
    avg_assets_per_vuln = total_relationships / len(vulns)
    
    print(f"\n3. Relationship Statistics:")
    print(f"   - Total vuln → asset relationships: {total_relationships}")
    print(f"   - Average assets per vulnerability: {avg_assets_per_vuln:.1f}")
    print(f"   - Expected API calls per poll cycle:")
    print(f"     * Step 0 (Get IDs): 1 call")
    print(f"     * Step 1 (Vuln details): {recent_count} calls")
    print(f"     * Step 2 (Asset details): ~{int(recent_count * avg_assets_per_vuln)} calls")
    print(f"     * TOTAL: ~{1 + recent_count + int(recent_count * avg_assets_per_vuln)} API calls")
    
    print("\n" + "=" * 60)
    print("✅ Data generation complete!")
    print("\nNext steps:")
    print("1. Start the Flask API: python app_nested.py")
    print("2. Test endpoints:")
    print("   curl 'http://localhost:5000/api/vulnerabilities/ids' -H 'Authorization: cvebuster-nested-key'")
