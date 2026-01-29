import asyncio
from app.db.database import execute_readonly_query

async def main():
    print("Searching for queries with markups...")
    try:
        # Find raw markups
        q = """
        SELECT qm.user_mobile, qam.markup_value, qam.query_id
        FROM query_activity_markups qam 
        JOIN query_masters qm ON qam.query_id = qm.query_id 
        LIMIT 5
        """
        rows = await execute_readonly_query(q, {})
        
        if rows:
            print(f"Found {len(rows)} markups:")
            for r in rows:
                print(f" - Mobile: {r['user_mobile']}, Value: {r['markup_value']}, QID: {r['query_id']}")
                
            # Check if this mobile is an admin
            mobile = rows[0]['user_mobile']
            q_admin = "SELECT * FROM master_admins WHERE phone = :m"
            admin_rows = await execute_readonly_query(q_admin, {"m": mobile})
            if admin_rows:
                print(f"✅ GOOD NEWS: User {mobile} is ALSO an Admin.")
            else:
                print(f"⚠️ NOTE: User {mobile} is NOT in master_admins table.")
        else:
            print("❌ No markups found in database.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
