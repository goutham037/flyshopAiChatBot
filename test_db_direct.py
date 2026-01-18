
import asyncio
import aiomysql
import logging
import traceback
import socket

# Enable full debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('aiomysql')
logger.setLevel(logging.DEBUG)

# Direct connection without URL string
DB_CONFIG = {
    "host": "82.25.121.78",
    "port": 3306,
    "user": "u271850780_crm",
    "password": "=l7OsdtiqUC",
    "db": "u271850780_crm_api",
    "connect_timeout": 10
}

async def test_direct_connection():
    print("=" * 60)
    print("DATABASE CONNECTION TEST - FULL LOGS")
    print("=" * 60)
    
    # Get local IP
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        print(f"Your Local IP: {local_ip}")
    except:
        print("Could not determine local IP")
    
    print(f"Target Host: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print(f"User: {DB_CONFIG['user']}")
    print(f"Database: {DB_CONFIG['db']}")
    print(f"Password: {'*' * len(DB_CONFIG['password'])}")
    print("-" * 60)
    
    # Test TCP connectivity first
    print("\n[Step 1] Testing TCP connectivity...")
    try:
        sock = socket.create_connection((DB_CONFIG['host'], DB_CONFIG['port']), timeout=10)
        sock.close()
        print("✅ TCP connection to port 3306 successful")
    except Exception as e:
        print(f"❌ TCP connection failed: {e}")
        return
    
    # Test MySQL connection
    print("\n[Step 2] Testing MySQL authentication...")
    try:
        conn = await aiomysql.connect(**DB_CONFIG)
        print("✅ MySQL connection successful!")
        
        async with conn.cursor() as cursor:
            await cursor.execute("SHOW TABLES")
            tables = await cursor.fetchall()
            print(f"\n✅ Found {len(tables)} tables:")
            for t in tables[:10]:
                print(f"   - {t[0]}")
        
        conn.close()
        
    except Exception as e:
        print(f"\n❌ MySQL connection failed!")
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {e}")
        print("\n--- Full Traceback ---")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_direct_connection())
