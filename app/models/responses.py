"""
Pydantic response models for the MVP Query API.
"""
from pydantic import BaseModel, Field
from typing import Optional, Any, Union
from enum import Enum


class ErrorCode(str, Enum):
    """Standardized error codes."""
    UNAUTHORIZED = "UNAUTHORIZED"
    UNKNOWN_INTENT = "UNKNOWN_INTENT"
    AMBIGUOUS_INTENT = "AMBIGUOUS_INTENT"
    AMBIGUOUS_ENTITY = "AMBIGUOUS_ENTITY"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    LLM_ERROR = "LLM_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class QueryMetadata(BaseModel):
    """Metadata about the query result."""
    rows: int = Field(description="Number of rows returned")
    sql: Optional[str] = Field(default=None, description="Sanitized query shape (placeholders shown)")


class QueryResponse(BaseModel):
    """Success response for POST /mvp/query."""
    success: bool = True
    intent: Optional[str] = Field(default=None, description="Detected intent")
    entities: Optional[dict[str, Any]] = Field(default=None, description="Extracted entities")
    data: Optional[Union[list[dict[str, Any]], dict[str, Any]]] = Field(default=None, description="Query result data")
    summary: Optional[str] = Field(default=None, description="Human-friendly summary")
    metadata: Optional[QueryMetadata] = Field(default=None, description="Query metadata")


class ErrorResponse(BaseModel):
    """Error response for POST /mvp/query."""
    success: bool = False
    error_code: ErrorCode
    message: str = Field(description="Human-readable error message")
    
    
# Intent types enum for type safety
class Intent(str, Enum):
    """Supported intents for the MVP."""
    BOOKING_STATUS = "booking_status"
    LIST_BOOKINGS = "list_bookings"
    QUOTATION_DETAIL = "quotation_detail"
    LIST_QUOTATIONS = "list_quotations"
    PAYMENT_STATUS = "payment_status"
    LIST_PAYMENTS = "list_payments"
    PAYMENT_SCHEDULE = "payment_schedule"
    ACTIVITY_STATUS = "activity_status"
    ADMIN_INFO = "admin_info"
    MESSAGE_HISTORY = "message_history"
    QUERY_SUMMARY = "query_summary"
    LIST_QUERIES = "list_queries"
    # General chat intents
    GREETING = "greeting"
    GENERAL_HELP = "general_help"
    UNKNOWN = "unknown"

