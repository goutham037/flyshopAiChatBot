import asyncio
from app.db.database import execute_readonly_query

async def main():
    try:
        # Check tables
        rows = await execute_readonly_query("SHOW TABLES", {})
        print("TABLES FOUND (ALL):")
        for r in rows:
             print(list(r.values())[0])
             
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
