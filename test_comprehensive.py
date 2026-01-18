"""
Comprehensive Test Suite for FlyShop AI ChatBot
100+ test cases covering all features
"""
import asyncio
import json
import time
from datetime import datetime
from typing import Optional

# Test categories
TEST_CASES = [
    # ========== GREETINGS (10 tests) ==========
    {"id": 1, "category": "greeting", "query": "Hi", "lang": "en", "expected_intent": "greeting"},
    {"id": 2, "category": "greeting", "query": "Hello", "lang": "en", "expected_intent": "greeting"},
    {"id": 3, "category": "greeting", "query": "Hey there", "lang": "en", "expected_intent": "greeting"},
    {"id": 4, "category": "greeting", "query": "Good morning", "lang": "en", "expected_intent": "greeting"},
    {"id": 5, "category": "greeting", "query": "नमस्ते", "lang": "hi", "expected_intent": "greeting"},
    {"id": 6, "category": "greeting", "query": "Namaste", "lang": "hi", "expected_intent": "greeting"},
    {"id": 7, "category": "greeting", "query": "హలో", "lang": "te", "expected_intent": "greeting"},
    {"id": 8, "category": "greeting", "query": "Kaise ho", "lang": "hinglish", "expected_intent": "greeting"},
    {"id": 9, "category": "greeting", "query": "Hi, how are you?", "lang": "en", "expected_intent": "greeting"},
    {"id": 10, "category": "greeting", "query": "Kem cho", "lang": "other", "expected_intent": "greeting"},
    
    # ========== LIST QUERIES (10 tests) ==========
    {"id": 11, "category": "list_queries", "query": "Show my queries", "lang": "en", "expected_intent": "list_queries"},
    {"id": 12, "category": "list_queries", "query": "List all my travel requests", "lang": "en", "expected_intent": "list_queries"},
    {"id": 13, "category": "list_queries", "query": "What bookings do I have", "lang": "en", "expected_intent": "list_queries"},
    {"id": 14, "category": "list_queries", "query": "मेरी सारी बुकिंग दिखाओ", "lang": "hi", "expected_intent": "list_queries"},
    {"id": 15, "category": "list_queries", "query": "naa details cheppu", "lang": "te", "expected_intent": "list_queries"},
    {"id": 16, "category": "list_queries", "query": "నా వివరాలు చూపించు", "lang": "te", "expected_intent": "list_queries"},
    {"id": 17, "category": "list_queries", "query": "Meri saari queries batao", "lang": "hinglish", "expected_intent": "list_queries"},
    {"id": 18, "category": "list_queries", "query": "Show me everything", "lang": "en", "expected_intent": "list_queries"},
    {"id": 19, "category": "list_queries", "query": "What do you know about me", "lang": "en", "expected_intent": "list_queries"},
    {"id": 20, "category": "list_queries", "query": "My profile details", "lang": "en", "expected_intent": "list_queries"},
    
    # ========== LIST PAYMENTS (10 tests) ==========
    {"id": 21, "category": "list_payments", "query": "Show my payments", "lang": "en", "expected_intent": "list_payments"},
    {"id": 22, "category": "list_payments", "query": "List all payments", "lang": "en", "expected_intent": "list_payments"},
    {"id": 23, "category": "list_payments", "query": "मेरी पेमेंट दिखाओ", "lang": "hi", "expected_intent": "list_payments"},
    {"id": 24, "category": "list_payments", "query": "naa payments cheppu", "lang": "te", "expected_intent": "list_payments"},
    {"id": 25, "category": "list_payments", "query": "Payment history", "lang": "en", "expected_intent": "list_payments"},
    {"id": 26, "category": "list_payments", "query": "Mera payment status", "lang": "hinglish", "expected_intent": "list_payments"},
    {"id": 27, "category": "list_payments", "query": "నా చెల్లింపులు", "lang": "te", "expected_intent": "list_payments"},
    {"id": 28, "category": "list_payments", "query": "How much have I paid", "lang": "en", "expected_intent": "list_payments"},
    {"id": 29, "category": "list_payments", "query": "Pending payments", "lang": "en", "expected_intent": "list_payments"},
    {"id": 30, "category": "list_payments", "query": "Kitna pay kiya maine", "lang": "hinglish", "expected_intent": "list_payments"},
    
    # ========== LIST QUOTATIONS (10 tests) ==========
    {"id": 31, "category": "list_quotations", "query": "Show my quotations", "lang": "en", "expected_intent": "list_quotations"},
    {"id": 32, "category": "list_quotations", "query": "List all quotes", "lang": "en", "expected_intent": "list_quotations"},
    {"id": 33, "category": "list_quotations", "query": "मेरे कोटेशन दिखाओ", "lang": "hi", "expected_intent": "list_quotations"},
    {"id": 34, "category": "list_quotations", "query": "naa quotations cheppu", "lang": "te", "expected_intent": "list_quotations"},
    {"id": 35, "category": "list_quotations", "query": "My price quotes", "lang": "en", "expected_intent": "list_quotations"},
    {"id": 36, "category": "list_quotations", "query": "Quotation list", "lang": "en", "expected_intent": "list_quotations"},
    {"id": 37, "category": "list_quotations", "query": "Pending quotations", "lang": "en", "expected_intent": "list_quotations"},
    {"id": 38, "category": "list_quotations", "query": "Confirmed quotes", "lang": "en", "expected_intent": "list_quotations"},
    {"id": 39, "category": "list_quotations", "query": "కొటేషన్లు చూపించు", "lang": "te", "expected_intent": "list_quotations"},
    {"id": 40, "category": "list_quotations", "query": "Mera quotation kya hai", "lang": "hinglish", "expected_intent": "list_quotations"},
    
    # ========== LIST BOOKINGS (10 tests) ==========
    {"id": 41, "category": "list_bookings", "query": "Show my bookings", "lang": "en", "expected_intent": "list_bookings"},
    {"id": 42, "category": "list_bookings", "query": "My flight bookings", "lang": "en", "expected_intent": "list_bookings"},
    {"id": 43, "category": "list_bookings", "query": "List all my flights", "lang": "en", "expected_intent": "list_bookings"},
    {"id": 44, "category": "list_bookings", "query": "मेरी फ्लाइट बुकिंग", "lang": "hi", "expected_intent": "list_bookings"},
    {"id": 45, "category": "list_bookings", "query": "naa bookings", "lang": "te", "expected_intent": "list_bookings"},
    {"id": 46, "category": "list_bookings", "query": "Flight tickets", "lang": "en", "expected_intent": "list_bookings"},
    {"id": 47, "category": "list_bookings", "query": "Meri flight ka detail", "lang": "hinglish", "expected_intent": "list_bookings"},
    {"id": 48, "category": "list_bookings", "query": "Upcoming flights", "lang": "en", "expected_intent": "list_bookings"},
    {"id": 49, "category": "list_bookings", "query": "నా విమాన బుకింగ్", "lang": "te", "expected_intent": "list_bookings"},
    {"id": 50, "category": "list_bookings", "query": "Travel bookings", "lang": "en", "expected_intent": "list_bookings"},
    
    # ========== QUERY SUMMARY WITH ID (10 tests) ==========
    {"id": 51, "category": "query_summary", "query": "Show query 817118", "lang": "en", "expected_intent": "query_summary", "has_entity": "query_id"},
    {"id": 52, "category": "query_summary", "query": "Status of FS817118", "lang": "en", "expected_intent": "query_summary", "has_entity": "query_id"},
    {"id": 53, "category": "query_summary", "query": "817118 ka status", "lang": "hinglish", "expected_intent": "query_summary", "has_entity": "query_id"},
    {"id": 54, "category": "query_summary", "query": "817118 status cheppu", "lang": "te", "expected_intent": "query_summary", "has_entity": "query_id"},
    {"id": 55, "category": "query_summary", "query": "Query number 433942", "lang": "en", "expected_intent": "query_summary", "has_entity": "query_id"},
    {"id": 56, "category": "query_summary", "query": "Details of 952141", "lang": "en", "expected_intent": "query_summary", "has_entity": "query_id"},
    {"id": 57, "category": "query_summary", "query": "433942 ki details", "lang": "hinglish", "expected_intent": "query_summary", "has_entity": "query_id"},
    {"id": 58, "category": "query_summary", "query": "FS1234 booking status", "lang": "en", "expected_intent": "query_summary", "has_entity": "query_id"},
    {"id": 59, "category": "query_summary", "query": "क्वेरी 817118", "lang": "hi", "expected_intent": "query_summary", "has_entity": "query_id"},
    {"id": 60, "category": "query_summary", "query": "817118", "lang": "en", "expected_intent": "query_summary", "has_entity": "query_id"},
    
    # ========== PAYMENT STATUS WITH ID (10 tests) ==========
    {"id": 61, "category": "payment_status", "query": "Payment for 817118", "lang": "en", "expected_intent": "payment_status", "has_entity": "query_id"},
    {"id": 62, "category": "payment_status", "query": "433942 ka payment", "lang": "hinglish", "expected_intent": "payment_status", "has_entity": "query_id"},
    {"id": 63, "category": "payment_status", "query": "Payment status of FS817118", "lang": "en", "expected_intent": "payment_status", "has_entity": "query_id"},
    {"id": 64, "category": "payment_status", "query": "817118 payment cheppu", "lang": "te", "expected_intent": "payment_status", "has_entity": "query_id"},
    {"id": 65, "category": "payment_status", "query": "How much paid for 433942", "lang": "en", "expected_intent": "payment_status", "has_entity": "query_id"},
    {"id": 66, "category": "payment_status", "query": "433942 ki payment details", "lang": "hinglish", "expected_intent": "payment_status", "has_entity": "query_id"},
    {"id": 67, "category": "payment_status", "query": "Pending amount for query 817118", "lang": "en", "expected_intent": "payment_status", "has_entity": "query_id"},
    {"id": 68, "category": "payment_status", "query": "817118 की पेमेंट", "lang": "hi", "expected_intent": "payment_status", "has_entity": "query_id"},
    {"id": 69, "category": "payment_status", "query": "952141 payment kya hai", "lang": "hinglish", "expected_intent": "payment_status", "has_entity": "query_id"},
    {"id": 70, "category": "payment_status", "query": "433942 చెల్లింపు", "lang": "te", "expected_intent": "payment_status", "has_entity": "query_id"},
    
    # ========== MISSING PARAMS - CLARIFICATION (15 tests) ==========
    {"id": 71, "category": "clarification", "query": "Show payment status", "lang": "en", "expected_clarify": True},
    {"id": 72, "category": "clarification", "query": "What's my booking status", "lang": "en", "expected_clarify": True},
    {"id": 73, "category": "clarification", "query": "मेरी बुकिंग का स्टेटस", "lang": "hi", "expected_clarify": True},
    {"id": 74, "category": "clarification", "query": "Quotation detail dikhao", "lang": "hinglish", "expected_clarify": True},
    {"id": 75, "category": "clarification", "query": "Activity status cheppu", "lang": "te", "expected_clarify": True},
    {"id": 76, "category": "clarification", "query": "3", "lang": "en", "expected_clarify": True},
    {"id": 77, "category": "clarification", "query": "Flight ka PNR", "lang": "hinglish", "expected_clarify": True},
    {"id": 78, "category": "clarification", "query": "Booking confirmation", "lang": "en", "expected_clarify": True},
    {"id": 79, "category": "clarification", "query": "Query status check karo", "lang": "hinglish", "expected_clarify": True},
    {"id": 80, "category": "clarification", "query": "నా బుకింగ్ స్థితి", "lang": "te", "expected_clarify": True},
    {"id": 81, "category": "clarification", "query": "Payment pending hai", "lang": "hinglish", "expected_clarify": True},
    {"id": 82, "category": "clarification", "query": "Quotation confirm ho gaya", "lang": "hinglish", "expected_clarify": True},
    {"id": 83, "category": "clarification", "query": "PNR number kya hai", "lang": "hinglish", "expected_clarify": True},
    {"id": 84, "category": "clarification", "query": "Is my booking done", "lang": "en", "expected_clarify": True},
    {"id": 85, "category": "clarification", "query": "Trip status", "lang": "en", "expected_clarify": True},
    
    # ========== GENERAL HELP / CHAT (15 tests) ==========
    {"id": 86, "category": "general_help", "query": "How can you help me", "lang": "en", "expected_intent": "general_help"},
    {"id": 87, "category": "general_help", "query": "What can you do", "lang": "en", "expected_intent": "general_help"},
    {"id": 88, "category": "general_help", "query": "Best time to visit Goa", "lang": "en", "expected_intent": "general_help"},
    {"id": 89, "category": "general_help", "query": "How to book a flight", "lang": "en", "expected_intent": "general_help"},
    {"id": 90, "category": "general_help", "query": "Dubai trip plan", "lang": "en", "expected_intent": "general_help"},
    {"id": 91, "category": "general_help", "query": "I want to plan a trip", "lang": "en", "expected_intent": "general_help"},
    {"id": 92, "category": "general_help", "query": "Thailand ya Bali kahan jaye", "lang": "hinglish", "expected_intent": "general_help"},
    {"id": 93, "category": "general_help", "query": "Visa requirements for Dubai", "lang": "en", "expected_intent": "general_help"},
    {"id": 94, "category": "general_help", "query": "Best hotels in Maldives", "lang": "en", "expected_intent": "general_help"},
    {"id": 95, "category": "general_help", "query": "Thank you for your help", "lang": "en", "expected_intent": "general_help"},
    {"id": 96, "category": "general_help", "query": "ధన్యవాదాలు", "lang": "te", "expected_intent": "general_help"},
    {"id": 97, "category": "general_help", "query": "Talk to me in Telugu only", "lang": "en", "expected_intent": "general_help"},
    {"id": 98, "category": "general_help", "query": "Aap kya kar sakte ho", "lang": "hinglish", "expected_intent": "general_help"},
    {"id": 99, "category": "general_help", "query": "मदद करो", "lang": "hi", "expected_intent": "general_help"},
    {"id": 100, "category": "general_help", "query": "I need help", "lang": "en", "expected_intent": "general_help"},
    
    # ========== ADMIN INFO (5 tests) ==========
    {"id": 101, "category": "admin_info", "query": "Who is my sales agent", "lang": "en", "expected_intent": "admin_info"},
    {"id": 102, "category": "admin_info", "query": "Contact my agent", "lang": "en", "expected_intent": "admin_info"},
    {"id": 103, "category": "admin_info", "query": "Sales executive contact", "lang": "en", "expected_intent": "admin_info"},
    {"id": 104, "category": "admin_info", "query": "मेरा एजेंट कौन है", "lang": "hi", "expected_intent": "admin_info"},
    {"id": 105, "category": "admin_info", "query": "Agent ka number", "lang": "hinglish", "expected_intent": "admin_info"},
    
    # ========== QUOTATION DETAIL (5 tests) ==========
    {"id": 106, "category": "quotation_detail", "query": "Show quotation QT772898", "lang": "en", "expected_intent": "quotation_detail", "has_entity": "quotation_id"},
    {"id": 107, "category": "quotation_detail", "query": "QT616045 ki details", "lang": "hinglish", "expected_intent": "quotation_detail", "has_entity": "quotation_id"},
    {"id": 108, "category": "quotation_detail", "query": "Quotation QT772898 status", "lang": "en", "expected_intent": "quotation_detail", "has_entity": "quotation_id"},
    {"id": 109, "category": "quotation_detail", "query": "QT772898 confirm hai", "lang": "hinglish", "expected_intent": "quotation_detail", "has_entity": "quotation_id"},
    {"id": 110, "category": "quotation_detail", "query": "QT616045 చూపించు", "lang": "te", "expected_intent": "quotation_detail", "has_entity": "quotation_id"},
]

async def run_single_test(test_case: dict) -> dict:
    """Run a single test case and return results."""
    from app.core.intent_extractor import extract_intent_and_entities
    
    test_id = test_case["id"]
    query = test_case["query"]
    expected_intent = test_case.get("expected_intent")
    expected_clarify = test_case.get("expected_clarify", False)
    has_entity = test_case.get("has_entity")
    
    start_time = time.time()
    
    try:
        result = await extract_intent_and_entities(query)
        latency_ms = (time.time() - start_time) * 1000
        
        # Check intent match
        intent_match = result.intent == expected_intent if expected_intent else True
        
        # Check clarification
        clarify_match = result.clarification_needed == expected_clarify if expected_clarify else True
        
        # Check entity extraction
        entity_match = True
        if has_entity:
            entity_match = has_entity in result.entities and result.entities[has_entity]
        
        # Overall pass
        passed = intent_match and clarify_match and entity_match
        
        return {
            "id": test_id,
            "category": test_case["category"],
            "query": query,
            "expected_lang": test_case["lang"],
            "expected_intent": expected_intent,
            "actual_intent": result.intent,
            "actual_lang": result.response_language,
            "clarification_needed": result.clarification_needed,
            "entities": result.entities,
            "intent_match": intent_match,
            "clarify_match": clarify_match,
            "entity_match": entity_match,
            "passed": passed,
            "latency_ms": round(latency_ms, 1),
            "friendly_message": result.friendly_message[:100] + "..." if len(result.friendly_message) > 100 else result.friendly_message
        }
        
    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        return {
            "id": test_id,
            "category": test_case["category"],
            "query": query,
            "passed": False,
            "error": str(e),
            "latency_ms": round(latency_ms, 1)
        }

async def run_all_tests():
    """Run all test cases and generate report."""
    print("=" * 80)
    print("FlyShop AI ChatBot - Comprehensive Test Suite")
    print(f"Running {len(TEST_CASES)} test cases...")
    print("=" * 80)
    
    results = []
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(TEST_CASES):
        result = await run_single_test(test_case)
        results.append(result)
        
        status = "✅" if result["passed"] else "❌"
        if result["passed"]:
            passed += 1
        else:
            failed += 1
        
        # Print progress
        print(f"{status} Test {result['id']:3d} [{result['category']:20s}] - {result.get('actual_intent', 'ERROR'):20s} ({result['latency_ms']:6.1f}ms)")
        
        # Brief pause to avoid rate limiting
        if (i + 1) % 10 == 0:
            print(f"\n--- Progress: {i+1}/{len(TEST_CASES)} ---\n")
            await asyncio.sleep(0.5)
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total:  {len(TEST_CASES)}")
    print(f"Passed: {passed} ({passed/len(TEST_CASES)*100:.1f}%)")
    print(f"Failed: {failed} ({failed/len(TEST_CASES)*100:.1f}%)")
    
    # Category breakdown
    print("\n--- By Category ---")
    categories = {}
    for r in results:
        cat = r["category"]
        if cat not in categories:
            categories[cat] = {"passed": 0, "total": 0}
        categories[cat]["total"] += 1
        if r["passed"]:
            categories[cat]["passed"] += 1
    
    for cat, stats in sorted(categories.items()):
        pct = stats["passed"] / stats["total"] * 100
        print(f"  {cat:20s}: {stats['passed']:2d}/{stats['total']:2d} ({pct:.0f}%)")
    
    # Average latency
    latencies = [r["latency_ms"] for r in results if "latency_ms" in r]
    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    print(f"\nAverage Latency: {avg_latency:.1f}ms")
    
    # Save results to file
    output = {
        "timestamp": datetime.now().isoformat(),
        "total_tests": len(TEST_CASES),
        "passed": passed,
        "failed": failed,
        "pass_rate": f"{passed/len(TEST_CASES)*100:.1f}%",
        "avg_latency_ms": round(avg_latency, 1),
        "categories": categories,
        "results": results
    }
    
    with open("test_results.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\nDetailed results saved to: test_results.json")
    
    # Show failed tests
    if failed > 0:
        print("\n--- FAILED TESTS ---")
        for r in results:
            if not r["passed"]:
                print(f"  #{r['id']}: {r['query'][:50]}...")
                if "error" in r:
                    print(f"       Error: {r['error']}")
                else:
                    print(f"       Expected: {r.get('expected_intent')} | Got: {r.get('actual_intent')}")
    
    return output

if __name__ == "__main__":
    asyncio.run(run_all_tests())
