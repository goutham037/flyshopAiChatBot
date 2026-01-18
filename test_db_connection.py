
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os
from pathlib import Path

# Load .env manually
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key] = value

DATABASE_URL = os.environ.get("DATABASE_URL")
print(f"DATABASE_URL from env: {DATABASE_URL}")

async def test_connection():
    if not DATABASE_URL:
        print("❌ DATABASE_URL not found in environment")
        return
        
    print(f"Testing connection to: {DATABASE_URL[:60]}...")
    
    try:
        engine = create_async_engine(DATABASE_URL, echo=False, connect_args={"connect_timeout": 10})
        
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            print(f"✅ Connection successful! Result: {result.scalar()}")
            
            # Try to get table count
            result = await conn.execute(text("SHOW TABLES"))
            tables = result.fetchall()
            print(f"✅ Found {len(tables)} tables in database")
            for t in tables[:10]:
                print(f"   - {t[0]}")
            if len(tables) > 10:
                print(f"   ... and {len(tables) - 10} more")
                
        await engine.dispose()
        
    except Exception as e:
        print(f"❌ Connection failed: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())
