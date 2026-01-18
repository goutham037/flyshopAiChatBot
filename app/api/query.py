"""
Query API endpoint: POST /mvp/query
Main endpoint for natural language customer queries.
"""
from fastapi import APIRouter, HTTPException
from typing import Union
import logging
import time
import asyncio
import json

from app.models.requests import QueryRequest
from app.models.responses import QueryResponse, ErrorResponse, ErrorCode
from app.config import get_settings
from app.core.intent_extractor import extract_intent_and_entities, generate_summary, get_model
from app.core.query_planner import create_query_plan, QueryPlan, QueryPlanError
from app.core.response_formatter import (
    create_success_response,
    create_error_response,
    mask_mobile
)
from app.db.database import validate_mobile_exists, execute_readonly_query
# from app.core.mock_data import validate_mock_mobile

router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()


async def fetch_universal_context(mobile: str) -> dict:
    """Fetch all relevant user context from DB."""
    # Extract last 10 digits to handle prefix inconsistencies
    mobile_plain = mobile[-10:] if len(mobile) >= 10 else mobile
    params = {"m_wild": f"%{mobile_plain}"}
    
    # Define queries using LIKE for last 10 digits
    # 1. Fetch Profile & Query IDs first
    q_profile = "SELECT * FROM query_masters WHERE user_mobile LIKE :m_wild ORDER BY created_at DESC LIMIT 1"
    q_ids = "SELECT query_id FROM query_masters WHERE user_mobile LIKE :m_wild"
    
    r_profile_list = await execute_readonly_query(q_profile, params)
    r_ids_list = await execute_readonly_query(q_ids, params)
    
    profile = r_profile_list[0] if r_profile_list else {}
    query_ids = [str(row['query_id']) for row in r_ids_list]



    if not query_ids:
        return {
            "profile": profile,
            "recent_bookings": [], "recent_payments": [], "recent_quotations": [],
            "recent_queries": [], "recent_activities": [], "payment_schedules": [],
            "agent_info": {}
        }

    # 2. Fetch related data using found Query IDs
    # Using explicit IDs handles cases where mobile matching in subqueries might miss connections
    # strictly relying on repetitive sub-selects.
    ids_placeholder = ",".join([f"'{qid}'" for qid in query_ids])
    
    # We use explicit SQL construction because parameter list binding in raw SQL can be tricky 
    # across different DB drivers for IN clauses.
    
    q_bookings = f"SELECT * FROM query_flight_manages WHERE query_id IN ({ids_placeholder}) ORDER BY departure_datetime DESC LIMIT 5"
    
    # For payments, we want payments linked to any of the user's query_ids. 
    # Note: query_payments usually links via query_id directly.
    q_payments = f"SELECT * FROM query_payments WHERE query_id IN ({ids_placeholder}) LIMIT 5"
    
    q_quotes = f"SELECT * FROM query_quotations WHERE query_id IN ({ids_placeholder}) ORDER BY sent_at DESC LIMIT 5"
    q_queries = f"SELECT * FROM query_masters WHERE query_id IN ({ids_placeholder}) ORDER BY created_at DESC LIMIT 5"
    
    q_activities = f"SELECT * FROM query_activities WHERE query_id IN ({ids_placeholder}) ORDER BY date ASC LIMIT 5"
    q_schedules = f"SELECT * FROM query_payment_schedulers WHERE query_id IN ({ids_placeholder}) ORDER BY payment_date ASC LIMIT 5"

    # Agent info (linked via admin_ref from profile)
    agent_ref = profile.get("admin_ref")
    q_agent = "SELECT * FROM master_admins WHERE m_code = :ref LIMIT 1" if agent_ref else None

    # Execute in parallel
    tasks = [
        execute_readonly_query(q_bookings, {}),
        execute_readonly_query(q_payments, {}),
        execute_readonly_query(q_quotes, {}),
        execute_readonly_query(q_queries, {}),
        execute_readonly_query(q_activities, {}),
        execute_readonly_query(q_schedules, {})
    ]
    if q_agent:
        tasks.append(execute_readonly_query(q_agent, {"ref": agent_ref}))

    results = await asyncio.gather(*tasks)
    
    # Unpack results
    r_bookings, r_payments, r_quotes, r_queries, r_activities, r_schedules = results[:6]
    r_agent = results[6] if q_agent else []



    return {
        "profile": profile,
        "recent_bookings": r_bookings,
        "recent_payments": r_payments, # Now fetching directly from query_payments without join redundancy
        "recent_quotations": r_quotes,
        "recent_queries": r_queries,
        "recent_activities": r_activities,
        "payment_schedules": r_schedules,
        "agent_info": r_agent[0] if r_agent else {}
    }

@router.get("/mvp/user-data")
async def get_user_data(mobile: str):
    """Fetch raw user data for the side panel."""
    if settings.USE_MOCK_DATA:
        return {"mock": "data"}
    
    mobile_exists = await validate_mobile_exists(mobile)
    if not mobile_exists and not len(mobile) >= 10:
         # Try flexible check just in case
        pass 

    try:
        data = await fetch_universal_context(mobile)
        return {"success": True, "data": data}
    except Exception as e:
        logger.error(f"Error fetching user data: {e}")
        return {"success": False, "error": str(e)}


@router.post(
    "/mvp/query",
    response_model=Union[QueryResponse, ErrorResponse],
    responses={
        200: {"model": QueryResponse, "description": "Successful query"},
        400: {"model": ErrorResponse, "description": "Bad request"},
    },
    summary="Execute a natural language query",
    description="Process a customer's query using Universal Context (no strict intent slots)."
)
async def query(request: QueryRequest) -> Union[QueryResponse, ErrorResponse]:
    """
    Universal Query Endpoint. Flow:
    1. Validate mobile.
    2. Fetch ALL relevant user context (Profile, Bookings, Payments, etc.) in parallel.
    3. Ask Gemini to answer the user query based on this comprehensive context.
    """
    start_time = time.time()
    masked_mobile = mask_mobile(request.mobile)
    
    try:
        # Step 1: Validate mobile exists
        # (Keeping existing validation logic)
        use_mock = settings.USE_MOCK_DATA
        logger.info(f"Universal Query from {masked_mobile}: {request.query[:50]}...")
        
        if use_mock:
            # Mock mode disabled/file removed
            mobile_exists = False
        else:
            mobile_exists = await validate_mobile_exists(request.mobile)
        
        if not mobile_exists:
            # Check if loose math works (last 10 digits logic embedded in fetch_universal_context acts as fallback lookup)
            # But strictly speaking we should validate. 
            # For now, we proceed if validation fails? No, earlier logic returned error.
            # But we saw `validate_mobile_exists` works with +91 if DB has +91.
            # Our fix in previous turn was updating `fetch_universal_context` queries to be loose.
            # We should probably keep validation strict or update it too. 
            pass

        if not mobile_exists:
             return create_error_response(ErrorCode.UNAUTHORIZED, "Mobile number not registered.")

        # Step 2: Fetch Universal Context (Parallel DB Fetches)
        context_data = {}
        if not use_mock:
            context_data = await fetch_universal_context(request.mobile)
            logger.info(f"Fetched Universal Context: {len(context_data.get('recent_bookings',[]))} bkg, {len(context_data.get('recent_payments',[]))} pay, {len(context_data.get('recent_quotations',[]))} qt, {len(context_data.get('recent_queries',[]))} qry, {len(context_data.get('recent_activities',[]))} act, {len(context_data.get('payment_schedules',[]))} sch")
            
        else:
            # Simple mock context
            context_data = {"mock": "data"}

        # Step 3: Generate Universal Response via Gemini
        # We reuse get_model from intent_extractor but strictly for generation
        
        model = get_model()
        
        prompt = f"""You are FlyShop's efficient, professional travel assistant.
The user is asking a question. You have their COMPLETE data below.

## USER CONTEXT (Database):
{json.dumps(context_data, default=str)}

## CONVERSATION HISTORY:
{json.dumps(request.conversation_context or [], default=str)}

## USER QUESTION:
"{request.query}"

## INSTRUCTIONS:
1. **Analyze** the user's question against the Data.
2. **Check ALL Sections**:
   - `recent_activities`: Contains Hotel/Activity bookings (look here for "Dubai", "Manali", etc).
   - `payment_schedules`: Contains the specific installments/dates for payments (Check here for "Payment Schedule").
   - `recent_payments`: Contains overall ledger/invoice totals.
   - `recent_bookings`: Contains Flight PNRs.
3. **Answer Directly**: e.g., "Your Dubai activity is confirmed for Dec 30." or "You have a payment of 25,000 due."
4. **No Robot Speak**: Do not say "Based on the database...".
5. **Professional Tone**: No emojis. Clear, concise facts.
6. **Language**: Reply in the same language as the user's question.

Answer:"""
        
        loop = asyncio.get_running_loop()
        response_obj = await loop.run_in_executor(None, lambda: model.generate_content(prompt))
        answer_text = response_obj.text.strip() if response_obj.text else "I couldn't generate an answer."
        
        # Log the raw results as requested
        logger.info(f"DB QUERY RESULT (Universal Context):\n{str(context_data)[:1000]}...\n-------------------")
        logger.info(f"GEMINI RAW RESPONSE:\n{answer_text}\n-------------------")

        # Create generic response
        return create_success_response(
            intent="universal_query",
            entities={},
            data=context_data, # Send full context to frontend for debugging context if needed
            sanitized_sql="[UNIVERSAL FETCH]",
            summary=answer_text
        )

    except Exception as e:
        logger.exception(f"Universal Query Error: {e}")
        return create_error_response(ErrorCode.INTERNAL_ERROR, "An error occurred.")


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "flyshop-ai-chatbot",
        "mock_mode": settings.USE_MOCK_DATA
    }


@router.get("/intents")
async def list_intents():
    """List supported intents (for documentation/debugging)."""
    from app.core.sql_templates import SQL_TEMPLATES
    
    intents = []
    for intent_key, template in SQL_TEMPLATES.items():
        intents.append({
            "intent": intent_key.value if hasattr(intent_key, 'value') else str(intent_key),
            "description": template["description"],
            "required_entities": template["required_entities"],
            "optional_entities": template["optional_entities"]
        })
    
    return {"intents": intents, "mock_mode": settings.USE_MOCK_DATA}


@router.get("/mock-users")
async def list_mock_users():
    """List available mock users for testing."""
    return {"error": "Mock mode is disabled and mock data file is removed."}


@router.get("/users")
async def list_users():
    """Fetch real users from database for dropdown."""
    if settings.USE_MOCK_DATA:
        # Map mock user format to standard format
        mock_data = await list_mock_users()
        if "mock_users" in mock_data:
            return {"users": mock_data["mock_users"]}
        return {"users": []}
        
    try:
        # Fetch distinct users, preferring most recent
        query = """
        SELECT DISTINCT user_name, user_mobile, created_at
        FROM query_masters 
        WHERE user_mobile IS NOT NULL 
        ORDER BY created_at DESC 
        LIMIT 100
        """
        rows = await execute_readonly_query(query, {})
        
        users = []
        seen_mobiles = set()
        
        for row in rows:
            mobile = row.get('user_mobile')
            if mobile and mobile not in seen_mobiles:
                users.append({
                    "name": row.get('user_name') or "Unknown",
                    "mobile": mobile
                })
                seen_mobiles.add(mobile)
                
        return {"users": users}
        
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        return {"users": [], "error": str(e)}

