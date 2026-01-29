import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_query(mode="user"):
    print(f"\nTesting Mode: {mode}")
    payload = {
        "mobile": "+919819355300", # Vijay Sharma (from DB samples)
        "query": "What is my latest booking status?",
        "mode": mode
    }
    
    try:
        response = requests.post(f"{BASE_URL}/mvp/query", json=payload)
        if response.status_code == 200:
            data = response.json()
            # print(f"Full Response: {json.dumps(data, indent=2)}")
            
            user_data = data.get("data", {})
            has_markups = "markups" in user_data
            
            if mode == "admin":
                if has_markups:
                    print(f"✅ PASS: Admin Mode contains 'markups'. Count: {len(user_data['markups'])}")
                else:
                    print(f"❌ FAIL: Admin Mode MISSING 'markups'")
            else:
                if not has_markups:
                    print(f"✅ PASS: User Mode does NOT contain 'markups'")
                else:
                    print(f"❌ FAIL: User Mode LEAKED 'markups'")
                    
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_query(mode="user")
    test_query(mode="admin")
