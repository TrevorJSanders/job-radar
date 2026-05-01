import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def test_endpoint(method, path, body=None):
    url = f"{BASE_URL}{path}"
    print(f"Testing {method} {url}...")
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=body)
        elif method == "PATCH":
            response = requests.patch(url, json=body)
        elif method == "DELETE":
            response = requests.delete(url)
        else:
            return False, 0, "Unsupported method"
            
        status_code = response.status_code
        try:
            resp_json = response.json()
            resp_str = json.dumps(resp_json)
        except:
            resp_str = response.text
            
        truncated_json = (resp_str[:200] + '...') if len(resp_str) > 200 else resp_str
        
        is_pass = 200 <= status_code < 300
        print(f"  Status: {status_code}")
        print(f"  JSON: {truncated_json}")
        print(f"  RESULT: {'PASS' if is_pass else 'FAIL'}")
        print("-" * 40)
        
        return is_pass, status_code, resp_json
    except Exception as e:
        print(f"  ERROR: {e}")
        print(f"  RESULT: FAIL")
        print("-" * 40)
        return False, 0, str(e)

def run_tests():
    passed = 0
    total = 12
    test_id = None
    
    # 1. GET /health
    ok, _, _ = test_endpoint("GET", "/health")
    if ok: passed += 1
    
    # 2. GET /dashboard/stats
    ok, _, _ = test_endpoint("GET", "/dashboard/stats")
    if ok: passed += 1
    
    # 3. GET /dashboard/applications-by-status
    ok, _, _ = test_endpoint("GET", "/dashboard/applications-by-status")
    if ok: passed += 1
    
    # 4. GET /applications
    ok, _, _ = test_endpoint("GET", "/applications")
    if ok: passed += 1
    
    # 5. POST /applications
    app_body = { "company": "Test Corp", "role": "Test Engineer", "source": "manual" }
    ok, _, resp = test_endpoint("POST", "/applications", body=app_body)
    if ok:
        passed += 1
        test_id = resp.get("id")
    
    # 6. GET /applications/{id}
    if test_id:
        ok, _, _ = test_endpoint("GET", f"/applications/{test_id}")
        if ok: passed += 1
    else:
        print("Skipping GET /applications/{id} - No ID from POST")
        
    # 7. PATCH /applications/{id}
    if test_id:
        patch_body = { "status": "screening", "notes": "Test note" }
        ok, _, _ = test_endpoint("PATCH", f"/applications/{test_id}", body=patch_body)
        if ok: passed += 1
    else:
        print("Skipping PATCH /applications/{id} - No ID from POST")
        
    # 8. GET /queue
    ok, _, _ = test_endpoint("GET", "/queue")
    if ok: passed += 1
    
    # 9. GET /queue/count
    ok, _, _ = test_endpoint("GET", "/queue/count")
    if ok: passed += 1
    
    # 10. GET /poll/status
    ok, _, _ = test_endpoint("GET", "/poll/status")
    if ok: passed += 1
    
    # 11. GET /applications (Confirm update)
    ok, _, resp = test_endpoint("GET", "/applications")
    if ok:
        # Check if Test Corp is in screening
        found = any(a.get("company") == "Test Corp" and a.get("status") == "screening" for a in resp)
        if found:
            print("  Verified: Test Corp found with status 'screening'")
            passed += 1
        else:
            print("  Failed: Test Corp not found with updated status")
            
    # 12. DELETE /applications/{id}
    if test_id:
        ok, _, _ = test_endpoint("DELETE", f"/applications/{test_id}")
        if ok: passed += 1
    else:
        print("Skipping DELETE /applications/{id} - No ID from POST")
        
    print(f"\nFINAL SUMMARY: {passed}/{total} endpoints passing")
    
    if passed < total:
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
