import asyncio
from app.db.database import execute_readonly_query

async def main():
    try:
        query = """
        SELECT qm.user_name, qm.user_mobile 
        FROM query_activity_markups qam
        JOIN query_masters qm ON qam.query_id = qm.query_id
        LIMIT 5
        """
        rows = await execute_readonly_query(query, {})
        
        if rows:
            print("Found Markups for these users:")
            for r in rows:
                print(f" - Name: {r['user_name']}, Mobile: {r['user_mobile']}")
        else:
            print("Markups exist but maybe orphan (not linked to query_masters).")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
