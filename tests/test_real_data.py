
import httpx
import json
import asyncio
from datetime import datetime

API_URL = "http://127.0.0.1:8000/mvp/query"

# COMPREHENSIVE TEST SUITE - All 11 Intents
# Using REAL mobile numbers and query IDs from the database

# Real users from db_schema_and_samples.json
USERS = {
    "mitul": {"mobile": "+919820301212", "name": "Mitul Pandya", "query_id": "817118"},
    "abu": {"mobile": "+918530955786", "name": "Abu Hamid", "query_id": "966381"},
    "vijay": {"mobile": "+919819355300", "name": "Vijay Sharma", "query_id": "391757"},
    "jaswant": {"mobile": "+919882444728", "name": "Jaswant Singh", "query_id": "694644"},
}

# Comprehensive test cases covering ALL intents
ALL_TESTS = [
    # ===========================================
    # 1. QUERY_SUMMARY - Consolidated query view
    # ===========================================
    {
        "category": "QUERY_SUMMARY",
        "name": "Query Summary for Mitul (817118)",
        "mobile": USERS["mitul"]["mobile"],
        "query": "Show me the summary of query 817118",
        "expected_intent": "query_summary"
    },
    {
        "category": "QUERY_SUMMARY",
        "name": "Query Summary - Implicit (just ID)",
        "mobile": USERS["mitul"]["mobile"],
        "query": "817118",
        "expected_intent": "query_summary"
    },
    
    # ===========================================
    # 2. BOOKING_STATUS - Flight booking status
    # ===========================================
    {
        "category": "BOOKING_STATUS",
        "name": "Booking Status for Query",
        "mobile": USERS["mitul"]["mobile"],
        "query": "Show my booking for 817118",
        "expected_intent": "booking_status"
    },
    {
        "category": "BOOKING_STATUS",
        "name": "Flight Status Variation",
        "mobile": USERS["vijay"]["mobile"],
        "query": "What is my flight status for 391757?",
        "expected_intent": "booking_status"
    },
    
    # ===========================================
    # 3. LIST_BOOKINGS - All bookings
    # ===========================================
    {
        "category": "LIST_BOOKINGS",
        "name": "List All Bookings",
        "mobile": USERS["mitul"]["mobile"],
        "query": "Show all my bookings",
        "expected_intent": "list_bookings"
    },
    
    # ===========================================
    # 4. QUOTATION_DETAIL - Specific quotation
    # ===========================================
    {
        "category": "QUOTATION_DETAIL",
        "name": "Quotation Details for Query",
        "mobile": USERS["mitul"]["mobile"],
        "query": "Show quotation details for 817118",
        "expected_intent": "quotation_detail"
    },
    
    # ===========================================
    # 5. LIST_QUOTATIONS - All quotations
    # ===========================================
    {
        "category": "LIST_QUOTATIONS",
        "name": "List All Quotations",
        "mobile": USERS["vijay"]["mobile"],
        "query": "List all my quotations",
        "expected_intent": "list_quotations"
    },
    
    # ===========================================
    # 6. PAYMENT_STATUS - Payment for a query
    # ===========================================
    {
        "category": "PAYMENT_STATUS",
        "name": "Payment Status for Query",
        "mobile": USERS["mitul"]["mobile"],
        "query": "What is the payment status for 817118?",
        "expected_intent": "payment_status"
    },
    
    # ===========================================
    # 7. LIST_PAYMENTS - All payments
    # ===========================================
    {
        "category": "LIST_PAYMENTS",
        "name": "List All Payments",
        "mobile": USERS["mitul"]["mobile"],
        "query": "List all my payments",
        "expected_intent": "list_payments"
    },
    {
        "category": "LIST_PAYMENTS",
        "name": "Show Payments Variation",
        "mobile": USERS["vijay"]["mobile"],
        "query": "Show my payment history",
        "expected_intent": "list_payments"
    },
    
    # ===========================================
    # 8. PAYMENT_SCHEDULE - Scheduled payments
    # ===========================================
    {
        "category": "PAYMENT_SCHEDULE",
        "name": "Payment Schedule for Query",
        "mobile": USERS["mitul"]["mobile"],
        "query": "What is the payment schedule for 817118?",
        "expected_intent": "payment_schedule"
    },
    
    # ===========================================
    # 9. ACTIVITY_STATUS - Activity/tour status
    # ===========================================
    {
        "category": "ACTIVITY_STATUS",
        "name": "Activity Status for Query",
        "mobile": USERS["mitul"]["mobile"],
        "query": "Check activity status for 817118",
        "expected_intent": "activity_status"
    },
    {
        "category": "ACTIVITY_STATUS",
        "name": "Tour Status Variation",
        "mobile": USERS["vijay"]["mobile"],
        "query": "What is my tour package status for 391757?",
        "expected_intent": "activity_status"
    },
    
    # ===========================================
    # 10. ADMIN_INFO - Sales executive contact
    # ===========================================
    {
        "category": "ADMIN_INFO",
        "name": "Admin Info for Query",
        "mobile": USERS["mitul"]["mobile"],
        "query": "Who is my sales executive for 817118?",
        "expected_intent": "admin_info"
    },
    {
        "category": "ADMIN_INFO",
        "name": "Contact Info Variation",
        "mobile": USERS["vijay"]["mobile"],
        "query": "Get my agent contact for 391757",
        "expected_intent": "admin_info"
    },
    
    # ===========================================
    # 11. MESSAGE_HISTORY - WhatsApp messages
    # ===========================================
    {
        "category": "MESSAGE_HISTORY",
        "name": "Message History",
        "mobile": USERS["mitul"]["mobile"],
        "query": "Show my WhatsApp message history",
        "expected_intent": "message_history"
    },
    
    # ===========================================
    # EDGE CASES & NATURAL LANGUAGE VARIATIONS
    # ===========================================
    {
        "category": "EDGE_CASE",
        "name": "Typo Tolerance - paymnt",
        "mobile": USERS["mitul"]["mobile"],
        "query": "what is the paymnt status for 817118",
        "expected_intent": "payment_status"
    },
    {
        "category": "EDGE_CASE",
        "name": "Mixed Case Query",
        "mobile": USERS["mitul"]["mobile"],
        "query": "SHOW ME MY BOOKINGS",
        "expected_intent": "list_bookings"
    },
    {
        "category": "EDGE_CASE",
        "name": "Missing query_id for list",
        "mobile": USERS["mitul"]["mobile"],
        "query": "show booking",
        "expected_intent": "list_bookings"
    },
    
    # ===========================================
    # SECURITY TESTS
    # ===========================================
    {
        "category": "SECURITY",
        "name": "SQL Injection Attempt",
        "mobile": USERS["mitul"]["mobile"],
        "query": "DROP TABLE users;",
        "expected_intent": None,  # Should be UNKNOWN_INTENT
        "expect_success": False
    },
    {
        "category": "SECURITY",
        "name": "Cross-User Access - Wrong Query",
        "mobile": USERS["mitul"]["mobile"],  # Mitul trying to access Vijay's query
        "query": "Show summary for 391757",  # 391757 belongs to Vijay (+919819355300)
        "expected_intent": "query_summary",
        "expect_data_count": 0  # Should return 0 records due to mobile scoping
    },
     {
        "category": "SECURITY",
        "name": "Write Operation Blocked",
        "mobile": USERS["mitul"]["mobile"],
        "query": "Delete my booking 817118",
        "expected_intent": None,
        "expect_success": False
    },
]


async def run_comprehensive_tests():
    """Run all tests and generate report."""
    results = {"passed": 0, "failed": 0, "tests": []}
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        print("=" * 70)
        print("COMPREHENSIVE API TEST SUITE - REAL DATABASE")
        print(f"Started: {datetime.now().isoformat()}")
        print("=" * 70)
        
        current_category = None
        
        for test in ALL_TESTS:
            # Print category header
            if test["category"] != current_category:
                current_category = test["category"]
                print(f"\n>>> {current_category}")
                print("-" * 60)
            
            print(f"\nTEST: {test['name']}")
            print(f"Query: \"{test['query']}\"")
            
            payload = {"mobile": test['mobile'], "query": test['query']}
            
            try:
                response = await client.post(API_URL, json=payload)
                res = response.json()
                
                success = res.get('success')
                intent = res.get('intent')
                data_count = len(res.get('data', []))
                
                # Determine pass/fail
                passed = True
                reasons = []
                
                # Check expected intent
                if test.get('expected_intent'):
                    if intent != test['expected_intent']:
                        passed = False
                        reasons.append(f"Intent: expected {test['expected_intent']}, got {intent}")
                
                # Check expected success
                if 'expect_success' in test:
                    if success != test['expect_success']:
                        passed = False
                        reasons.append(f"Success: expected {test['expect_success']}, got {success}")
                
                # Check expected data count
                if 'expect_data_count' in test:
                    if data_count != test['expect_data_count']:
                        passed = False
                        reasons.append(f"Data count: expected {test['expect_data_count']}, got {data_count}")
                
                # Print result
                if passed:
                    print(f"✅ PASS | Intent: {intent} | Data: {data_count} records")
                    results["passed"] += 1
                else:
                    print(f"❌ FAIL | {', '.join(reasons)}")
                    results["failed"] += 1
                
                # Print summary if available
                if res.get('summary') and success:
                    print(f"   Summary: {res['summary'][:100]}...")
                
                results["tests"].append({
                    "name": test['name'],
                    "category": test['category'],
                    "passed": passed,
                    "intent": intent,
                    "data_count": data_count
                })
                    
            except Exception as e:
                print(f"❌ ERROR: {e}")
                results["failed"] += 1
                results["tests"].append({
                    "name": test['name'],
                    "category": test['category'],
                    "passed": False,
                    "error": str(e)
                })
        
        # Print summary
        print("\n" + "=" * 70)
        print(f"TEST SUMMARY: {results['passed']}/{results['passed'] + results['failed']} Passed")
        print("=" * 70)
        
        # Save results to file
        with open("test_results.json", "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to test_results.json")
        
        return results


if __name__ == "__main__":
    asyncio.run(run_comprehensive_tests())
