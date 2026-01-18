from app.models.responses import QueryResponse
import json

def test_query_response():
    # Test with list
    r1 = QueryResponse(data=[{"id": 1}], intent="test")
    print("List data: OK")
    
    # Test with dict
    r2 = QueryResponse(data={"id": 1}, intent="test")
    print("Dict data: OK")
    
    print("All checks passed")

if __name__ == "__main__":
    try:
        test_query_response()
    except Exception as e:
        print(f"FAILED: {e}")
