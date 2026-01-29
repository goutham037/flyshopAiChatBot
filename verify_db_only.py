import requests
import json
import urllib.parse

BASE_URL = "http://127.0.0.1:8000"

def test_user_data(mobile):
    print(f"\nTesting Data for: {mobile}")
    encoded_mobile = urllib.parse.quote(mobile)
    url = f"{BASE_URL}/mvp/user-data?mobile={encoded_mobile}"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                profile = data.get("data", {}).get("profile", {})
                print(f"✅ Success! Found user: {profile.get('user_name')}")
                print(f"   Admin Ref in Profile: {profile.get('admin_ref')}")
                print(f"   Agent Info: {data.get('data', {}).get('agent_info')}")
                print(f"   Bookings: {len(data.get('data', {}).get('recent_bookings', []))}")
            else:
                 print(f"❌ Failed: {data.get('error')}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_user_data("+919819355300")
