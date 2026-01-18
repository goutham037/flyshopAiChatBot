"""
Script to query available users from the database.
Run: python query_users.py
"""
import asyncio
import sys
import os

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def get_users():
    from app.db.database import get_db_session
    from sqlalchemy import text
    
    try:
        async with get_db_session() as session:
            # Get users from User table
            print("=== Users from User table ===")
            result = await session.execute(
                text("SELECT name, user_mobile FROM User WHERE user_mobile IS NOT NULL LIMIT 10")
            )
            users = result.fetchall()
            for u in users:
                print(f"  {u[0]}: {u[1]}")
            
            print("\n=== Users from QueryMaster (distinct) ===")
            result2 = await session.execute(
                text("SELECT DISTINCT user_name, user_mobile FROM QueryMaster WHERE user_mobile IS NOT NULL LIMIT 10")
            )
            qm_users = result2.fetchall()
            for u in qm_users:
                print(f"  {u[0]}: {u[1]}")
                
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure your .env file is configured with:")
        print("  DATABASE_URL=mysql+aiomysql://user:password@host:port/database")
        print("  GEMINI_API_KEY=your_key")

if __name__ == "__main__":
    asyncio.run(get_users())
