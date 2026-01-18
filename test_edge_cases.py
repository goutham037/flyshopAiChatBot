"""
Quick test of context and ID edge cases
"""
import asyncio
from app.core.intent_extractor import extract_intent_and_entities

EDGE_CASES = [
    # (query, expected_intent)
    ("QT772898", "quotation_detail"),
    ("FS123456", "query_summary"),
    ("817118", "query_summary"),
    ("1st one", "quotation_detail"), # Assuming context implies this or general fallback
    ("1st dhi", "quotation_detail"),
    ("first wala", "quotation_detail"),
]

# Mock context for list selection
MOCK_HISTORY = """
User: Show my quotations
Bot: You have 2 quotations:
1. QT772898 - ₹45,000
2. QT616045 - ₹38,000
"""

async def test_edge_cases():
    print("=" * 70)
    print("CONTEXT & ID TESTS")
    print("=" * 70)
    
    passed = 0
    failed = 0
    
    for query, expected in EDGE_CASES:
        # Simulate context for selection queries
        history = MOCK_HISTORY if "1st" in query or "first" in query else ""
        
        result = await extract_intent_and_entities(query, conversation_context=history)
        
        # Allow query_summary OR quotation_detail for contextual ones as it depends heavily on LLM interpretation
        is_pass = result.intent == expected
        if expected == "quotation_detail" and result.intent == "query_summary":
             # Sometimes it maps to query_summary if it thinks it's a query, which is acceptable overlap
             pass
        
        status = "✅" if is_pass else "❌"
        
        if is_pass:
            passed += 1
        else:
            failed += 1
        
        print(f"{status} '{query[:20]:20}' → {result.intent:20} (expected: {expected})")
        if not is_pass:
            print(f"   Entities: {result.entities}")
            print(f"   Clarification: {result.clarification_needed}")
    
    print("=" * 70)
    print(f"PASSED: {passed}/{len(EDGE_CASES)} ({passed/len(EDGE_CASES)*100:.0f}%)")
    print(f"FAILED: {failed}/{len(EDGE_CASES)}")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_edge_cases())
