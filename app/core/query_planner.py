"""
Query Planner: Selects and prepares SQL templates based on intent and entities.
Handles template selection, parameter binding, and query execution orchestration.
"""
from typing import Optional
import logging

from app.core.sql_templates import get_template, get_required_entities
from app.core.sql_validator import validate_parameters, SQLValidationError
from app.core.intent_extractor import IntentExtractionResult
from app.models.responses import ErrorCode

logger = logging.getLogger(__name__)


class QueryPlan:
    """Represents a prepared query plan ready for execution."""
    
    def __init__(
        self,
        intent: str,
        sql: str,
        sanitized_sql: str,
        params: dict,
    ):
        self.intent = intent
        self.sql = sql
        self.sanitized_sql = sanitized_sql
        self.params = params


class QueryPlanError:
    """Represents an error in query planning."""
    
    def __init__(self, error_code: ErrorCode, message: str):
        self.error_code = error_code
        self.message = message


def create_query_plan(
    extraction_result: IntentExtractionResult,
    mobile: str,
    limit: int = 50,
    offset: int = 0
) -> QueryPlan | QueryPlanError:
    """
    Create a query plan from the intent extraction result.
    
    Args:
        extraction_result: Result from intent extraction
        mobile: User's mobile number for scoping
        limit: Result limit
        offset: Result offset
        
    Returns:
        QueryPlan if successful, QueryPlanError otherwise
    """
    intent = extraction_result.intent
    entities = extraction_result.entities
    
    # Handle unknown intent
    if extraction_result.is_unknown():
        return QueryPlanError(
            error_code=ErrorCode.UNKNOWN_INTENT,
            message="I couldn't understand your request. Try asking about bookings, payments, quotations, or activities. For example: 'Show my booking for FS1234' or 'List my payments'."
        )
    
    # Get template for intent
    template = get_template(intent)
    if not template:
        return QueryPlanError(
            error_code=ErrorCode.UNKNOWN_INTENT,
            message=f"No template found for intent: {intent}"
        )
    
    # Check required entities
    required = template["required_entities"]
    missing = [e for e in required if e not in entities or not entities[e]]
    
    # For flexible multi-step flow: if query_id is missing, flag for fallback
    # instead of returning an error. The caller can then fetch user's queries.
    if missing and "query_id" in missing:
        # Return special fallback plan that signals "list user's queries first"
        return QueryPlanError(
            error_code=ErrorCode.AMBIGUOUS_ENTITY,
            message="FALLBACK_TO_LIST",  # Special marker for caller
            # The caller (query.py) will handle this by listing user's queries
        )
    elif missing:
        return QueryPlanError(
            error_code=ErrorCode.AMBIGUOUS_ENTITY,
            message=f"Please provide the following: {', '.join(missing)}."
        )
    
    # Build parameters
    params = {
        "mobile": mobile,
        "limit": limit,
        "offset": offset,
    }
    
    # Add extracted entities to params
    for key, value in entities.items():
        if value:
            params[key] = value
    
    # Validate parameters
    try:
        validated_params = validate_parameters(params)
    except SQLValidationError as e:
        return QueryPlanError(
            error_code=ErrorCode.VALIDATION_ERROR,
            message=str(e)
        )
    
    return QueryPlan(
        intent=intent,
        sql=template["query"],
        sanitized_sql=template["sanitized"],
        params=validated_params,
    )
