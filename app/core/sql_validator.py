"""
SQL Validator: Ensures SQL safety rules are enforced.
Only pre-defined templates are allowed - no dynamic SQL generation.
"""
import re
from typing import Optional

from app.config import get_settings
from app.core.schema_mapper import ALLOWED_TABLES, is_column_allowed

settings = get_settings()

# Blocked SQL keywords - these should never appear in our templates anyway
# but we validate just in case
BLOCKED_KEYWORDS = {
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE",
    "GRANT", "REVOKE", "CREATE", "EXEC", "EXECUTE"
}

# Pattern to detect multiple statements (semicolon injection)
MULTI_STATEMENT_PATTERN = re.compile(r';\s*\w', re.IGNORECASE)


class SQLValidationError(Exception):
    """Raised when SQL validation fails."""
    pass


def validate_sql_template(sql: str) -> bool:
    """
    Validate that a SQL template follows safety rules.
    This is mainly for development/testing - production uses pre-validated templates.
    
    Args:
        sql: The SQL query string (template)
        
    Returns:
        True if valid
        
    Raises:
        SQLValidationError: If validation fails
    """
    sql_upper = sql.upper()
    
    # Check for blocked keywords
    for keyword in BLOCKED_KEYWORDS:
        # Word boundary check to avoid false positives
        pattern = r'\b' + keyword + r'\b'
        if re.search(pattern, sql_upper):
            raise SQLValidationError(f"Blocked keyword detected: {keyword}")
    
    # Check for multiple statements (semicolon followed by more SQL)
    if MULTI_STATEMENT_PATTERN.search(sql):
        raise SQLValidationError("Multiple SQL statements not allowed")
    
    # Must start with SELECT
    if not sql_upper.strip().startswith("SELECT"):
        raise SQLValidationError("Only SELECT statements are allowed")
    
    return True


def validate_parameters(params: dict) -> dict:
    """
    Validate and sanitize query parameters.
    
    Args:
        params: Dictionary of parameter names and values
        
    Returns:
        Validated parameters dictionary
        
    Raises:
        SQLValidationError: If validation fails
    """
    validated = {}
    
    for key, value in params.items():
        # Limit validation
        if key == "limit":
            if not isinstance(value, int):
                try:
                    value = int(value)
                except (ValueError, TypeError):
                    raise SQLValidationError(f"Invalid limit value: {value}")
            value = min(value, settings.MAX_LIMIT)
            value = max(value, 1)
        
        # Offset validation
        elif key == "offset":
            if not isinstance(value, int):
                try:
                    value = int(value)
                except (ValueError, TypeError):
                    raise SQLValidationError(f"Invalid offset value: {value}")
            value = max(value, 0)
        
        # String values - ensure they're actual strings and not SQL injection attempts
        elif isinstance(value, str):
            # Trim whitespace
            value = value.strip()
            # Check for obvious injection patterns in string values
            if any(blocked in value.upper() for blocked in ["--", "/*", "*/"]):
                raise SQLValidationError(f"Invalid characters in parameter: {key}")
        
        validated[key] = value
    
    return validated


def sanitize_sql_for_display(sql: str) -> str:
    """
    Create a sanitized version of SQL for display in metadata.
    Replaces parameter placeholders with ? and normalizes whitespace.
    
    Args:
        sql: The SQL query template
        
    Returns:
        Sanitized SQL string for display
    """
    # Replace named parameters with ?
    sanitized = re.sub(r':\w+', '?', sql)
    
    # Normalize whitespace
    sanitized = ' '.join(sanitized.split())
    
    return sanitized
