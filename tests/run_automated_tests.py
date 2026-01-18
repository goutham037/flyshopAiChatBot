
import httpx
import json
import asyncio
import os

API_URL = "http://127.0.0.1:8000/mvp/query"
TEST_DATA_FILE = "tests/automated_test_cases.json"

async def run_tests():
    if not os.path.exists(TEST_DATA_FILE):
        print(f"Error: Test data file {TEST_DATA_FILE} not found.")
        return

    with open(TEST_DATA_FILE, 'r') as f:
        categories = json.load(f)

    async with httpx.AsyncClient(timeout=30.0) as client:
        print("====== STARTING AUTOMATED COMPREHENSIVE TESTING ======")
        
        total_tests = 0
        passed_tests = 0
        
        for category in categories:
            cat_name = category['category']
            print(f"\n\n>>> {cat_name}")
            print("=" * 60)
            
            for test in category['tests']:
                total_tests += 1
                input_text = test['input']
                mobile = test['mobile']
                exp_intent = test.get('expected_intent')
                exp_success = test.get('expected_success')
                exp_data_size = test.get('expected_data_size')
                note = test.get('note', '')
                
                print(f"\nTEST #{total_tests}: {input_text}")
                if note:
                    print(f"Goal: {note}")
                
                payload = {"mobile": mobile, "query": input_text}
                
                try:
                    response = await client.post(API_URL, json=payload)
                    res_json = response.json()
                    
                    # Validation Logic
                    verdict = "PASS"
                    fail_reasons = []
                    
                    # 1. Success Status
                    if res_json.get('success') != exp_success:
                        # Allow flexibility: if we expect False but get True with empty data/unknown intent, that might be okay depending on definition
                        # But strictly:
                        verdict = "FAIL"
                        fail_reasons.append(f"Success mismatch. Expected {exp_success}, got {res_json.get('success')}")
                    
                    # 2. Intent Check (if specified and success is true)
                    if exp_intent and res_json.get('intent') != exp_intent:
                         # Soft check for edge cases where intent might vary
                        if exp_intent == "booking_status" and res_json.get('intent') == "list_bookings":
                             pass # Tolerance
                        elif res_json.get('success') is False and exp_success is False:
                            pass # If we expected fail and it failed, intent doesn't matter much
                        else:
                            verdict = "FAIL"
                            fail_reasons.append(f"Intent mismatch. Expected {exp_intent}, got {res_json.get('intent')}")
                            
                    # 3. Data Size Check (Mock Data verification)
                    if exp_data_size is not None:
                        data = res_json.get('data', [])
                        if len(data) != exp_data_size:
                            verdict = "FAIL"
                            fail_reasons.append(f"Data size mismatch. Expected {exp_data_size}, got {len(data)}")

                    # Print Result
                    if verdict == "PASS":
                        print(f"✅ PASS | Intent: {res_json.get('intent')} | Data: {len(res_json.get('data', []))} records")
                        passed_tests += 1
                        if res_json.get('summary'):
                             print(f"   Summary: {res_json.get('summary')}")
                    else:
                        print(f"❌ FAIL | Reasons: {', '.join(fail_reasons)}")
                        print(f"   Full Response: {json.dumps(res_json, indent=2)}")

                except Exception as e:
                    print(f"❌ FAIL | Exception: {e}")
        
        print("\n" + "=" * 60)
        print(f"TEST SUMMARY: {passed_tests}/{total_tests} Passed")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_tests())
