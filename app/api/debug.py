from fastapi import APIRouter
from app.db.database import execute_readonly_query
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/debug/test-users")
async def get_test_users():
    """Get list of users with booking/quotation data for testing."""
    query = """
        SELECT 
            qm.user_mobile, qm.user_name, qm.query_id,
            (SELECT COUNT(*) FROM query_flight_manages qf WHERE qf.query_id = qm.query_id) as flights,
            (SELECT COUNT(*) FROM query_payments qp WHERE qp.query_id = qm.query_id) as payments,
            (SELECT COUNT(*) FROM query_quotations qq WHERE qq.query_id = qm.query_id) as quotations
        FROM query_masters qm
        ORDER BY qm.query_id DESC
        LIMIT 100
    """
    try:
        users = await execute_readonly_query(query, {})
        return {"users": users}
    except Exception as e:
        logger.error(f"Failed to fetch test users: {e}")
        return {"users": [], "error": str(e)}
