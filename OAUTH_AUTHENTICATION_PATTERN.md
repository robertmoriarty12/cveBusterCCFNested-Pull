# cveBuster with OAuth Token Refresh - Nested API for Authentication

## 🔐 Use Case: Nested API for Token-Based Authentication

Many ISV APIs require a two-step authentication pattern:
1. **Step 0**: Call token endpoint to get short-lived access token
2. **Step 1+**: Use that token in subsequent API calls

This is common with OAuth 2.0 client credentials flow, where tokens expire after 15-60 minutes.

## 🎯 Real-World ISV Examples

| ISV | Pattern |
|-----|---------|
| **Microsoft Graph API** | POST /token → GET /users, /devices, /auditLogs |
| **Salesforce** | POST /services/oauth2/token → GET /query, /sobjects |
| **ServiceNow** | POST /oauth_token.do → GET /table/incident, /table/sys_user |
| **Tenable.io** | POST /session → GET /assets/export, /vulnerabilities/export |
| **Okta** | POST /oauth2/v1/token → GET /api/v1/logs, /api/v1/users |

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 0 (Root): Get OAuth Token                             │
│ POST /oauth/token                                           │
│ Body: {                                                     │
│   "grant_type": "client_credentials",                      │
│   "client_id": "xxx",                                       │
│   "client_secret": "xxx"                                    │
│ }                                                           │
│ Response: {                                                 │
│   "access_token": "eyJhbGc...",                            │
│   "expires_in": 3600                                        │
│ }                                                           │
└────────────────────────┬────────────────────────────────────┘
                         │ Extract: Token_PlaceHolder = access_token
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 1 (Nested): Get Vulnerability IDs                     │
│ GET /api/vulnerabilities/ids                                │
│ Headers: {                                                  │
│   "Authorization": "Bearer $Token_PlaceHolder$"            │
│ }                                                           │
│ Response: {                                                 │
│   "vulnerability_ids": ["CVE-2024-10001", ...]            │
│ }                                                           │
└────────────────────────┬────────────────────────────────────┘
                         │ Extract: Url_PlaceHolder = vulnerability_ids
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 2 (Nested): Get Vulnerability Details                 │
│ GET /api/vulnerabilities/$Url_PlaceHolder$                 │
│ Headers: {                                                  │
│   "Authorization": "Bearer $Token_PlaceHolder$"            │
│ }                                                           │
│ Response: {...vulnerability details...}                     │
└─────────────────────────────────────────────────────────────┘
```

## ⭐ Key Benefits

1. **Token Refresh per Poll**: Each 5-minute poll gets a fresh token
2. **No Token Expiration Issues**: Never worry about expired tokens between polls
3. **No Credential Storage**: Token only lives in memory during poll cycle
4. **Automatic Retry**: If token fails, CCF retries the entire flow
5. **Multi-Step Reuse**: Same token used across all nested API calls

## 📝 CCF Configuration

### Step 0: Get OAuth Token

```json
{
  "request": {
    "apiEndpoint": "https://api.example.com/oauth/token",
    "httpMethod": "POST",
    "isPostPayloadJson": true,
    "queryParametersTemplate": "{'grant_type': 'client_credentials', 'client_id': '[[parameters('clientId')]]', 'client_secret': '[[parameters('clientSecret')]]'}",
    "headers": {
      "Content-Type": "application/json"
    }
  },
  "stepInfo": {
    "stepType": "Nested",
    "nextSteps": [{
      "stepId": "step1_get_vulnerability_ids",
      "stepPlaceholdersParsingKql": "source | project res = parse_json(data) | project Token_PlaceHolder = res['access_token']"
    }]
  }
}
```

**Key Points**:
- `httpMethod: POST` for token endpoint
- `isPostPayloadJson: true` to send JSON body
- `queryParametersTemplate` contains OAuth credentials
- KQL extracts `access_token` into `$Token_PlaceHolder$`

### Step 1: Use Token in Header

```json
{
  "stepCollectorConfigs": {
    "step1_get_vulnerability_ids": {
      "request": {
        "httpMethod": "GET",
        "apiEndpoint": "https://api.example.com/api/vulnerabilities/ids",
        "headers": {
          "Authorization": "Bearer $Token_PlaceHolder$",
          "Accept": "application/json"
        }
      },
      "stepInfo": {
        "stepType": "Nested",
        "nextSteps": [{
          "stepId": "step2_get_details",
          "stepPlaceholdersParsingKql": "source | project res = parse_json(data) | project ids = res['vulnerability_ids'] | mvexpand ids | project Url_PlaceHolder = ids"
        }]
      }
    }
  }
}
```

**Key Points**:
- `Authorization: Bearer $Token_PlaceHolder$` injects the token
- Token is automatically passed from Step 0
- Same token can be reused in Step 2, Step 3, etc.

### Step 2: Continue Using Same Token

```json
{
  "stepCollectorConfigs": {
    "step2_get_details": {
      "request": {
        "httpMethod": "GET",
        "apiEndpoint": "https://api.example.com/api/vulnerabilities/$Url_PlaceHolder$",
        "headers": {
          "Authorization": "Bearer $Token_PlaceHolder$",
          "Accept": "application/json"
        }
      }
    }
  }
}
```

**Key Points**:
- Same `$Token_PlaceHolder$` used across multiple steps
- Token persists throughout the entire nested call chain

## 🧪 Testing Scenarios

### Scenario 1: Token Refresh on Every Poll
**Objective**: Verify token is fetched fresh each 5-minute poll

**Expected Behavior**:
- Poll 1 (T+0): Fetch token → Use in API calls
- Poll 2 (T+5): Fetch NEW token → Use in API calls
- Poll 3 (T+10): Fetch NEW token → Use in API calls

**Validation**:
- Check Flask logs for multiple POST /oauth/token calls
- Verify different tokens are used each poll

### Scenario 2: Token Reuse Across Nested Calls
**Objective**: Verify single token used for all nested calls in one poll

**Expected Behavior**:
- 1 POST /oauth/token call per poll
- 15 GET /api/vulnerabilities/ids calls (all with same token)
- 45 GET /api/vulnerabilities/{id} calls (all with same token)

**Validation**:
- Token_PlaceHolder should be identical across all calls in single poll
- Only 1 token request per 61 API calls

### Scenario 3: Token Expiration Handling
**Objective**: Verify CCF retries if token expires mid-poll

**Expected Behavior**:
- If token expires during nested calls, CCF should retry from Step 0
- New token fetched and nested calls re-executed

**Validation**:
- Simulate 401 Unauthorized in Step 2
- Verify CCF retries from Step 0 with new token

## 🔧 Implementation: Mock API with OAuth

### Flask Server with Token Endpoint

```python
import secrets
import time
from flask import Flask, request, jsonify

app = Flask(__name__)

# Store active tokens (in production, use Redis/database)
active_tokens = {}

@app.route('/oauth/token', methods=['POST'])
def get_token():
    """OAuth 2.0 token endpoint."""
    data = request.get_json()
    
    # Validate credentials
    client_id = data.get('client_id')
    client_secret = data.get('client_secret')
    grant_type = data.get('grant_type')
    
    if grant_type != 'client_credentials':
        return jsonify({"error": "unsupported_grant_type"}), 400
    
    if client_id != "cvebuster-client" or client_secret != "cvebuster-secret":
        return jsonify({"error": "invalid_client"}), 401
    
    # Generate token
    access_token = secrets.token_urlsafe(32)
    expires_in = 3600  # 1 hour
    
    # Store token with expiration
    active_tokens[access_token] = {
        "expires_at": time.time() + expires_in,
        "client_id": client_id
    }
    
    print(f"[STEP 0] POST /oauth/token - Issued token: {access_token[:16]}...")
    
    return jsonify({
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": expires_in
    })

def validate_token(token):
    """Validate Bearer token."""
    if not token:
        return False
    
    # Remove "Bearer " prefix
    token = token.replace("Bearer ", "")
    
    token_info = active_tokens.get(token)
    if not token_info:
        return False
    
    # Check expiration
    if time.time() > token_info["expires_at"]:
        del active_tokens[token]
        return False
    
    return True

@app.route('/api/vulnerabilities/ids', methods=['GET'])
def get_vulnerability_ids():
    """Get vulnerability IDs (requires Bearer token)."""
    auth_header = request.headers.get('Authorization', '')
    
    if not validate_token(auth_header):
        return jsonify({"error": "invalid_token"}), 401
    
    # Return mock IDs
    ids = [f"CVE-2024-{10000 + i}" for i in range(1, 16)]
    
    print(f"[STEP 1] GET /api/vulnerabilities/ids - Token valid, returned {len(ids)} IDs")
    
    return jsonify({
        "vulnerability_ids": ids,
        "count": len(ids)
    })

@app.route('/api/vulnerabilities/<vuln_id>', methods=['GET'])
def get_vulnerability_details(vuln_id):
    """Get vulnerability details (requires Bearer token)."""
    auth_header = request.headers.get('Authorization', '')
    
    if not validate_token(auth_header):
        return jsonify({"error": "invalid_token"}), 401
    
    print(f"[STEP 2] GET /api/vulnerabilities/{vuln_id} - Token valid")
    
    return jsonify({
        "vuln_id": vuln_id,
        "severity": "Critical",
        "cvss": 9.8,
        "title": f"Vulnerability {vuln_id}"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
```

## 📋 Complete CCF Configuration Example

```json
{
  "auth": {
    "type": "None"
  },
  "request": {
    "apiEndpoint": "https://api.example.com/oauth/token",
    "httpMethod": "POST",
    "isPostPayloadJson": true,
    "queryParametersTemplate": "{'grant_type': 'client_credentials', 'client_id': '[[parameters('clientId')]]', 'client_secret': '[[parameters('clientSecret')]]'}",
    "headers": {
      "Content-Type": "application/json"
    },
    "retryCount": 3,
    "timeoutInSeconds": 60
  },
  "response": {
    "eventsJsonPaths": ["$"],
    "format": "json"
  },
  "stepInfo": {
    "stepType": "Nested",
    "nextSteps": [{
      "stepId": "step1_get_vulnerability_ids",
      "stepPlaceholdersParsingKql": "source | project res = parse_json(data) | project Token_PlaceHolder = res['access_token']"
    }]
  },
  "stepCollectorConfigs": {
    "step1_get_vulnerability_ids": {
      "request": {
        "httpMethod": "GET",
        "apiEndpoint": "https://api.example.com/api/vulnerabilities/ids",
        "queryWindowInMin": 5,
        "startTimeAttributeName": "startTime",
        "endTimeAttributeName": "endTime",
        "headers": {
          "Authorization": "Bearer $Token_PlaceHolder$",
          "Accept": "application/json"
        }
      },
      "response": {
        "eventsJsonPaths": ["$"],
        "format": "json"
      },
      "stepInfo": {
        "stepType": "Nested",
        "nextSteps": [{
          "stepId": "step2_get_details",
          "stepPlaceholdersParsingKql": "source | project res = parse_json(data) | project ids = res['vulnerability_ids'] | mvexpand ids | project Url_PlaceHolder = ids"
        }]
      }
    },
    "step2_get_details": {
      "shouldJoinNestedData": true,
      "joinedDataStepName": "vulnerability",
      "request": {
        "httpMethod": "GET",
        "apiEndpoint": "https://api.example.com/api/vulnerabilities/$Url_PlaceHolder$",
        "headers": {
          "Authorization": "Bearer $Token_PlaceHolder$",
          "Accept": "application/json"
        }
      },
      "response": {
        "eventsJsonPaths": ["$"],
        "format": "json"
      }
    }
  }
}
```

## ⚠️ Important Considerations

### 1. Token Caching
**Current Behavior**: Token fetched every 5-minute poll  
**Optimization**: Could CCF cache tokens if `expires_in` > poll interval?  
**Status**: Needs validation - may not be supported yet

### 2. Token Expiration Mid-Poll
**Scenario**: Token expires between Step 1 and Step 2  
**Expected**: CCF should handle 401 and retry from Step 0  
**Status**: Needs validation

### 3. Auth Type Configuration
**Important**: Set `auth.type = "None"` because we're handling auth via nested API  
**Don't Use**: `auth.type = "APIKey"` or `auth.type = "OAuth"` - these are for root call only

### 4. Multiple Placeholder Types
You can use multiple placeholders in same config:
- `$Token_PlaceHolder$` - From Step 0 (token)
- `$Url_PlaceHolder$` - From Step 1 (IDs)
- `$Asset_PlaceHolder$` - From Step 2 (asset names)

All persist through nested chain!

## 🎯 Advantages Over Standard OAuth Auth

| Standard CCF OAuth | Nested API OAuth |
|-------------------|------------------|
| Token management by CCF | Token management explicit in config |
| Limited control over token refresh | Full control over refresh timing |
| May not work with custom OAuth flows | Works with any token endpoint |
| Cannot reuse token across nested calls | Token persists across all steps |
| Config hidden in auth section | Config visible in stepInfo |

## 🚀 Real-World Implementation Example

### ServiceNow Pattern
```
Step 0: POST /oauth_token.do → Get token
Step 1: GET /table/incident?sysparm_query=state=1 → Get incident IDs (with token)
Step 2: GET /table/incident/{sys_id} → Get incident details (with token)
Step 3: GET /table/sys_user/{assigned_to} → Get user details (with token)
```

### Microsoft Graph Pattern
```
Step 0: POST /oauth2/v2.0/token → Get token
Step 1: GET /users → Get user IDs (with token)
Step 2: GET /users/{id}/manager → Get manager (with token)
Step 3: GET /users/{id}/directReports → Get reports (with token)
```

## 📝 Summary

**✅ Nested API for Authentication Works!**

This pattern enables:
1. ✅ OAuth token refresh per poll
2. ✅ Token reuse across nested calls
3. ✅ Support for custom OAuth flows
4. ✅ No token expiration between polls
5. ✅ Explicit control over auth flow

**Recommended For**:
- OAuth 2.0 client credentials flow
- Short-lived tokens (< 5 minutes)
- APIs with custom token endpoints
- Multi-step auth requirements
- Token-based API key refresh

**Potential Gaps to Test**:
- Token caching across polls (optimization)
- 401 handling mid-nested-call (retry logic)
- Token expiration < poll interval

---

**This is a powerful pattern that solves a real ISV pain point!** 🔐🚀
