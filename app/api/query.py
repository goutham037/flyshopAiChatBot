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



def sanitize_for_user_mode(data: dict):
    """Recursively strip sensitive admin fields for User Mode."""
    SENSITIVE_KEYS = {
        "supplier_price", "gross_profit", "markup_value", "markup_type",
        "supplier_amount", "supplier_recieved", "supplier_pending",
        "gross_markup_type", "gross_markup_value", "gst_on_markup",
        "supplier_id", "onward_supplier_price", "return_supplier_price"
    }
    
    # Remove top-level markups table
    data.pop("markups", None)
    
    # Recursive cleanup
    stack = [data]
    while stack:
        current = stack.pop()
        if isinstance(current, dict):
            # Remove keys
            for key in list(current.keys()):
                if key in SENSITIVE_KEYS:
                    current.pop(key)
                else:
                    val = current[key]
                    if isinstance(val, (dict, list)):
                        stack.append(val)
        elif isinstance(current, list):
            for item in current:
                if isinstance(item, (dict, list)):
                    stack.append(item)


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
        # If no profile, we can't link easily unless checking whatsapp table by mobile.
        pass

    ids_placeholder = ",".join([f"'{qid}'" for qid in query_ids]) if query_ids else "NULL"
    
    # Data Tables
    q_bookings = f"SELECT * FROM query_flight_manages WHERE query_id IN ({ids_placeholder}) ORDER BY departure_datetime DESC LIMIT 5"
    q_payments = f"SELECT * FROM query_payments WHERE query_id IN ({ids_placeholder}) LIMIT 5"
    q_quotes = f"SELECT * FROM query_quotations WHERE query_id IN ({ids_placeholder}) ORDER BY sent_at DESC LIMIT 5"
    q_queries = f"SELECT * FROM query_masters WHERE query_id IN ({ids_placeholder}) ORDER BY created_at DESC LIMIT 5"
    q_activities = f"SELECT * FROM query_activities WHERE query_id IN ({ids_placeholder}) ORDER BY date ASC LIMIT 5"
    q_schedules = f"SELECT * FROM query_payment_schedulers WHERE query_id IN ({ids_placeholder}) ORDER BY payment_date ASC LIMIT 5"
    q_markups = f"SELECT * FROM query_activity_markups WHERE query_id IN ({ids_placeholder}) LIMIT 10"

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
        execute_readonly_query(q_schedules, {}),
        execute_readonly_query(q_markups, {})
    ]
    if q_agent:
        tasks.append(execute_readonly_query(q_agent, {"ref": agent_ref}))

    results = await asyncio.gather(*tasks)
    
    # Unpack results
    r_bookings, r_payments, r_quotes, r_queries, r_activities, r_schedules, r_markups = results[:7]
    r_agent = results[7] if q_agent else []

    return {
        "profile": profile,
        "recent_bookings": r_bookings,
        "recent_payments": r_payments,
        "recent_quotations": r_quotes,
        "recent_queries": r_queries,
        "recent_activities": r_activities,
        "payment_schedules": r_schedules,
        "markups": r_markups,
        "agent_info": r_agent[0] if r_agent else {}
    }


async def fetch_global_context() -> dict:
    """Fetch GLOBAL context for All Users (Admin Mode)."""
    
    # Recent Global Activity (Last 20 items across the board)
    q_bookings = "SELECT * FROM query_flight_manages ORDER BY departure_datetime DESC LIMIT 20"
    q_payments = "SELECT * FROM query_payments ORDER BY id DESC LIMIT 20"
    q_queries =  "SELECT * FROM query_masters ORDER BY created_at DESC LIMIT 20"
    q_activities = "SELECT * FROM query_activities ORDER BY date DESC LIMIT 20"
    
    # Aggregates
    q_agg_payments = "SELECT SUM(recieved_amount) as total_revenue, SUM(pending_amount) as total_pending FROM query_payments"
    q_agg_queries = "SELECT COUNT(*) as total_queries, query_stage, COUNT(query_id) as count FROM query_masters GROUP BY query_stage"
    
    tasks = [
        execute_readonly_query(q_bookings, {}),
        execute_readonly_query(q_payments, {}),
        execute_readonly_query(q_queries, {}),
        execute_readonly_query(q_activities, {}),
        execute_readonly_query(q_agg_payments, {}),
        execute_readonly_query(q_agg_queries, {})
    ]
    
    results = await asyncio.gather(*tasks)
    
    r_bookings, r_payments, r_queries, r_activities, r_agg_pay, r_agg_qry = results
    
    return {
        "global_mode": True,
        "recent_bookings": r_bookings,
        "recent_payments": r_payments,
        "recent_queries": r_queries,
        "recent_activities": r_activities,
        "stats": {
            "total_revenue": r_agg_pay[0].get('total_revenue') if r_agg_pay else 0,
            "total_pending": r_agg_pay[0].get('total_pending') if r_agg_pay else 0,
            "query_stats": r_agg_qry
        }
    }


@router.get("/mvp/user-data")
async def get_user_data(mobile: str, mode: str = "user"):
    """Fetch raw user data for the side panel."""
    # Global Context Handling
    if mobile == "ALL":
        try:
            data = await fetch_global_context()
            return {"success": True, "data": data}
        except Exception as e:
            logger.error(f"Error fetching global data: {e}")
            return {"success": False, "error": str(e)}

    if settings.USE_MOCK_DATA:
        return {"mock": "data"}
    
    mobile_exists = await validate_mobile_exists(mobile)
    if not mobile_exists and not len(mobile) >= 10:
        pass 

    try:
        data = await fetch_universal_context(mobile)
        
        # Field-Level Security
        if mode != "admin":
            sanitize_for_user_mode(data)
            
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
    description="Process a customer's query using Universal Context."
)
async def query(request: QueryRequest) -> Union[QueryResponse, ErrorResponse]:
    """
    Universal Query Endpoint.
    """
    start_time = time.time()
    masked_mobile = mask_mobile(request.mobile)
    
    try:
        # Step 1: Validate mobile
        use_mock = settings.USE_MOCK_DATA
        logger.info(f"Universal Query from {masked_mobile}: {request.query[:50]}...")
        
        is_global = (request.mobile == "ALL" and request.mode == "admin")

        if use_mock:
            mobile_exists = True
        elif is_global:
            mobile_exists = True # Skip validation for global query
        else:
            mobile_exists = await validate_mobile_exists(request.mobile)
        
        if not mobile_exists:
             return create_error_response(ErrorCode.UNAUTHORIZED, "Mobile number not registered.")

        # Step 2: Fetch Context
        context_data = {}
        if not use_mock:
            if is_global:
                context_data = await fetch_global_context()
            else:
                context_data = await fetch_universal_context(request.mobile)
                # Field-Level Security
                if request.mode != 'admin':
                    sanitize_for_user_mode(context_data)
        else:
            context_data = {
                "profile": {"user_name": "Test User", "user_mobile": "+919999999999"},
                "recent_bookings": [{"pnr": "ABCDEF", "destination": "Dubai", "date": "2025-12-30"}]
            }

        # Step 3: Generate Response
        model = get_model()
        
        if request.mode == "admin":
            if is_global:
                 system_role = "You are a Senior Data Analyst for FlyShop."
                 recipient_context = "The Admin is asking about GLOBAL business stats (All Users)."
                 instructions = """
                 - You have access to `stats` (Total Revenue, Query Counts) and recent global lists.
                 - **Analyze Trends**: Use the recent lists to identify active destinations or booking trends.
                 - **Summarize**: Give high-level insights.
                 """
            else:
                system_role = "You are a travel assistant helping an ADMIN."
                recipient_context = f"The Admin is asking about user {masked_mobile}."
                instructions = """
                - Answer as if reporting to an Admin.
                - Refer to the customer as 'the user'.
                - **Profit/Margins**: You have access to `gross_profit`, `supplier_price`, and `markup_value`. Use them to calculate and explain margins if asked.
                """
        else:
            system_role = "You are FlyShop's efficient, professional travel assistant."
            recipient_context = "The user is asking a question."
            instructions = """
            - Answer directly to the customer.
            - Use 'You' to refer to the customer.
            - Do NOT discuss internal costs, supplier prices, or profits.
            """

        prompt = f"""{system_role}
{recipient_context}
You have their COMPLETE data below.

## USER CONTEXT (Database):
{json.dumps(context_data, default=str)}

## CONVERSATION HISTORY:
{json.dumps(request.conversation_context or [], default=str)}

## USER QUESTION:
"{request.query}"

## INSTRUCTIONS:
1. **Analyze** the user's question against the Data.
2. **Check ALL Sections**:
   - `recent_activities`: Hotel/Activity bookings.
   - `payment_schedules`: Payment installments.
   - `recent_payments`: Ledger/invoice totals.
   - `recent_bookings`: Flight PNRs.
3. {instructions.strip()}
4. **No Robot Speak**: Do not say "Based on the database...".
5. **Language**: Reply in the same language as the user's question.

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
        return create_error_response(ErrorCode.INTERNAL_ERROR, f"An error occurred: {str(e)}")


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
        # Return hardcoded mock users for testing
        return {"users": [
            {"name": "Test User", "mobile": "+919999999999"},
            {"name": "Admin User", "mobile": "+918888888888"}
        ]}
        
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


@router.get("/admins")
async def list_admins():
    """Fetch admins from database for dropdown."""
    if settings.USE_MOCK_DATA:
        return {"users": [
            {"name": "Mock Admin", "mobile": "+918888888888"}
        ]}
        
    try:
        # Fetch admins
        query = "SELECT name, phone as mobile FROM master_admins LIMIT 100"
        rows = await execute_readonly_query(query, {})
        
        admins = []
        for row in rows:
             admins.append({
                "name": row.get('name') or "Unknown",
                "mobile": row.get('mobile')
            })
                
        return {"users": admins}
        
    except Exception as e:
        logger.error(f"Error fetching admins: {e}")
        return {"users": [], "error": str(e)}

