
import asyncio
import sys
from app.db.database import execute_readonly_query

async def debug_user_data(mobile):
    print(f"--- Debugging Data for {mobile} ---")
    
    # 1. Check Profile / Query Masters
    q1 = "SELECT query_id, user_name FROM query_masters WHERE user_mobile = :m"
    rows1 = await execute_readonly_query(q1, {"m": mobile})
    print(f"Query Masters: found {len(rows1)} rows")
    if rows1:
        print(f"Sample Query IDs: {[r['query_id'] for r in rows1[:5]]}")
        
    # 2. Check Bookings (Query Flight Manages)
    q2 = """
    SELECT * FROM query_flight_manages 
    WHERE query_id IN (SELECT query_id FROM query_masters WHERE user_mobile = :m)
    """
    rows2 = await execute_readonly_query(q2, {"m": mobile})
    print(f"Flight Manages (via Subquery): found {len(rows2)} rows")
    
    # 3. Check Payments (Query Payments)
    q3 = """
    SELECT qp.* FROM query_payments qp 
    JOIN query_masters qm ON qp.query_id = qm.query_id 
    WHERE qm.user_mobile = :m
    """
    rows3 = await execute_readonly_query(q3, {"m": mobile})
    print(f"Payments (via Join): found {len(rows3)} rows")

    # 4. Check Tables directly (LIMIT 5) to see if tables are empty
    q4 = "SELECT count(*) as c FROM query_flight_manages"
    rows4 = await execute_readonly_query(q4, {})
    print(f"Total Rows in query_flight_manages: {rows4[0]['c']}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # Check specific user requested
    target_mobile = "7023429773" 
    print(f"Checking data for {target_mobile} (no prefix)...")
    asyncio.run(debug_user_data(target_mobile))
