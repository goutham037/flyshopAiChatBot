"""
Response Formatter: Formats query results and creates API responses.
Handles data transformation and response structure standardization.
"""
from typing import Optional, Any
from datetime import datetime, date
import logging

from app.models.responses import QueryResponse, QueryMetadata, ErrorResponse, ErrorCode

logger = logging.getLogger(__name__)


def format_row_value(value: Any) -> Any:
    """
    Format a single row value for JSON serialization.
    Handles datetime, date, and other types.
    """
    if isinstance(value, datetime):
        return value.isoformat()
    elif isinstance(value, date):
        return value.isoformat()
    elif isinstance(value, bytes):
        return value.decode('utf-8', errors='replace')
    return value


def format_data_recursively(data: Any) -> Any:
    """
    Recursively format data for JSON serialization.
    Handles dicts, lists, and primitive values.
    """
    if isinstance(data, dict):
        return {k: format_data_recursively(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [format_data_recursively(item) for item in data]
    else:
        return format_row_value(data)


def format_rows(rows: list[dict]) -> list[dict]:
    """
    Format all rows for JSON serialization.
    Kept for backward compatibility, but now uses recursive formatter.
    """
    if not isinstance(rows, list):
        # Fallback if someone passes a dict to this specific function
        return format_data_recursively(rows)
        
    return [format_data_recursively(row) for row in rows]


def create_success_response(
    intent: str,
    entities: dict,
    data: Any,
    sanitized_sql: str,
    summary: Optional[str] = None
) -> QueryResponse:
    """
    Create a successful query response.
    
    Args:
        intent: The detected intent
        entities: Extracted entities
        data: Query result data (can be list or dict)
        sanitized_sql: Sanitized SQL for metadata
        summary: Optional human-friendly summary
        
    Returns:
        QueryResponse object
    """
    formatted_data = format_data_recursively(data)
    
    # Calculate row count based on data type
    row_count = 0
    if isinstance(formatted_data, list):
        row_count = len(formatted_data)
    elif isinstance(formatted_data, dict):
        # For a single object or nested context, we can consider it 1 "result" set
        row_count = 1
    
    return QueryResponse(
        success=True,
        intent=intent,
        entities=entities,
        data=formatted_data,
        summary=summary,
        metadata=QueryMetadata(
            rows=row_count,
            sql=sanitized_sql
        )
    )


def create_error_response(error_code: ErrorCode, message: str) -> ErrorResponse:
    """
    Create an error response.
    
    Args:
        error_code: The error code
        message: Human-readable error message
        
    Returns:
        ErrorResponse object
    """
    return ErrorResponse(
        success=False,
        error_code=error_code,
        message=message
    )


def mask_mobile(mobile: str) -> str:
    """
    Mask mobile number for logging (show only last 4 digits).
    Example: +919999999999 -> +91******9999
    """
    if len(mobile) <= 4:
        return "****"
    return mobile[:3] + "*" * (len(mobile) - 7) + mobile[-4:]
