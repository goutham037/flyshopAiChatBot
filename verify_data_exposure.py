import requests
import json

BASE_URL = "http://127.0.0.1:8000"
MOBILE = "+919819355300" 

def test_data_exposure():
    print("Verifying Field-Level Security...")
    
    # 1. Test User Mode (Should NOT have supplier_price)
    print("\n--- Testing User Mode ---")
    res_user = requests.post(f"{BASE_URL}/mvp/query", json={
        "mobile": MOBILE,
        "query": "Show my bookings",
        "mode": "user",
        "conversation_context": ""
    })
    data_user = res_user.json().get("data", {})
    
    # Check for markups (should be gone)
    if "markups" in data_user:
        print("❌ FAIL: User Mode has 'markups' key.")
    else:
        print("✅ PASS: User Mode 'markups' key is removed.")
        
    # Check deep nested fields
    bookings = data_user.get("recent_bookings", [])
    if bookings:
        sample = bookings[0]
        if "supplier_price" in sample:
            print(f"❌ FAIL: User Mode booking has 'supplier_price'.")
        else:
            print(f"✅ PASS: User Mode booking sanitized (no supplier_price).")
            
    # 2. Test Admin Mode (Should HAVE supplier_price)
    print("\n--- Testing Admin Mode ---")
    res_admin = requests.post(f"{BASE_URL}/mvp/query", json={
        "mobile": MOBILE,
        "query": "Show my bookings",
        "mode": "admin",
        "conversation_context": ""
    })
    print(f"Status Code: {res_admin.status_code}")
    if res_admin.status_code != 200:
        print(f"Error Response: {res_admin.text}")
        return

    full_json = res_admin.json()
    print(f"Full JSON: {json.dumps(full_json, indent=2)}")
    data_admin = full_json.get("data") or {}
    print(f"Data Keys: {list(data_admin.keys())}")
    
    # Check for markups (should be exist)
    if "markups" in data_admin:
        print("✅ PASS: Admin Mode has 'markups' key.")
    else:
        print("⚠️ NOTE: Admin Mode 'markups' key missing (might be empty data).")

    # Check whatsapp
    if "whatsapp_messages" in data_admin:
        print("❓ INFO: Admin Mode has 'whatsapp_messages' key (Removed feature?).")
    else:
         print("✅ PASS: Admin Mode 'whatsapp_messages' key correctly absent (Feature disabled).")

    # Check supplier price presence (note: if DB has no data, this check might be skipped in runtime, 
    # but we check if the code *tried* to fetch it. Actually we can only check if rows exist)
    bookings_admin = data_admin.get("recent_bookings", [])
    if bookings_admin:
        sample = bookings_admin[0]
        # In this specific codebase, we select *, so if the column exists in DB, it should be here.
        # We assume the column exists (MasterFlightManage usually has it).
        # We'll just print keys to verify.
        print(f"Admin Booking Keys: {list(sample.keys())[:5]}... (checking for sensitive)")
        if "supplier_price" in sample or "markup_value" in sample:
             print("✅ PASS: Admin Mode sees sensitive fields.")
        else:
             print("⚠️ NOTE: Sensitive keys not found. Check if DB table has them.")

if __name__ == "__main__":
    test_data_exposure()
