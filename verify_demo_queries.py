import requests
import json

BASE_URL = "http://127.0.0.1:8000"
MOBILE = "+919819355300" 

def test_admin_query():
    print("\nTesting Admin Query (Expected to use Demo Data)...")
    payload = {
        "mobile": MOBILE,
        "query": "Who is this user and what is their email?",
        "mode": "admin",
        "conversation_context": ""
    }
    
    try:
        response = requests.post(f"{BASE_URL}/mvp/query", json=payload)
        if response.status_code == 200:
            data = response.json()
            summary = data.get("summary", "")
            print(f"🤖 Answer: {summary}")
            
            # Check for Demo Profile info in answer like "Demo Admin-User" or "demo@flyshop.in"
            if "Demo Admin-User" in summary or "demo@flyshop.in" in summary:
                print("✅ PASS: Gemini referenced the Demo Profile!")
            else:
                print("⚠️ WARNING: Gemini might not have used the demo profile. Check answer text.")

            # Check context data
            profile = data.get("data", {}).get("profile", {})
            if profile.get("user_name") == "Demo Admin-User":
                 print(f"✅ PASS: Response data contains Demo Profile.")
            else:
                 print(f"❌ FAIL: Response data missing Demo Profile. Got: {profile}")
                 
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_admin_query()
