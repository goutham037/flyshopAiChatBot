"""
Script to find users with complete booking data (flights, payments, etc.)
Uses synchronous PyMySQL directly.
"""
import pymysql
from app.config import get_settings

settings = get_settings()

def find_users_with_data():
    conn = pymysql.connect(
        host=settings.DB2_HOST,
        port=settings.DB2_PORT,
        user=settings.DB2_USERNAME,
        password=settings.DB2_PASSWORD,
        database=settings.DB2_DATABASE,
        cursorclass=pymysql.cursors.DictCursor
    )
    
    try:
        with conn.cursor() as cursor:
            query = """
                SELECT 
                    qm.user_mobile, qm.user_name, qm.query_id,
                    (SELECT COUNT(*) FROM query_flight_manages qf WHERE qf.query_id = qm.query_id) as flights,
                    (SELECT COUNT(*) FROM query_payments qp WHERE qp.query_id = qm.query_id) as payments,
                    (SELECT COUNT(*) FROM query_quotations qq WHERE qq.query_id = qm.query_id) as quotations
                FROM query_masters qm
                HAVING flights > 0 OR payments > 0 OR quotations > 0
                ORDER BY flights DESC, payments DESC, quotations DESC
                LIMIT 10
            """
            cursor.execute(query)
            results = cursor.fetchall()
            
            print("=" * 80)
            print("USERS WITH COMPLETE BOOKING DATA (for testing)")
            print("=" * 80)
            
            if not results:
                print("No users found with flight/payment/quotation data.")
            else:
                for r in results:
                    print(f"\nMobile: {r['user_mobile']}")
                    print(f"Name: {r['user_name']}")
                    print(f"Query ID: {r['query_id']}")
                    print(f"Flights: {r['flights']} | Payments: {r['payments']} | Quotations: {r['quotations']}")
                    print("-" * 40)
                    
    finally:
        conn.close()

if __name__ == "__main__":
    find_users_with_data()
