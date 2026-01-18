"""
Pydantic request models for the MVP Query API.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
import re


class QueryRequest(BaseModel):
    """Request model for POST /mvp/query endpoint."""
    
    mobile: str = Field(
        ...,
        description="Customer mobile number in format +91XXXXXXXXXX",
        examples=["+919999999999"]
    )
    query: str = Field(
        ...,
        description="Natural language query from the customer",
        min_length=1,
        max_length=500,
        examples=["Show my pending payments for query FS1902"]
    )
    conversation_context: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Optional conversation history for context-aware responses"
    )
    preferred_language: Optional[str] = Field(
        default=None,
        description="Preferred response language: 'en' (English), 'hi' (Hindi), 'hinglish' (mix). If set, all responses will be in this language.",
        examples=["en", "hi", "hinglish"]
    )
    limit: int = Field(
        default=50,
        ge=1,
        le=500,
        description="Maximum number of rows to return"
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Offset for pagination"
    )
    
    @field_validator("mobile")
    @classmethod
    def validate_mobile(cls, v: str) -> str:
        """Validate mobile number format."""
        # Remove spaces and normalize
        v = v.strip().replace(" ", "")
        
        # Check format: +91 followed by 10 digits OR just 10 digits
        # Allow inputs like 9876543210 (add +91) or +919876543210
        if re.match(r"^\d{10}$", v):
            return "+91" + v
            
        pattern = r"^\+91\d{10}$"
        if not re.match(pattern, v):
            raise ValueError("Mobile must be in format +91XXXXXXXXXX or XXXXXXXXXX (10 digits)")
        
        return v
    
    @field_validator("query")
    @classmethod
    def sanitize_query(cls, v: str) -> str:
        """Basic sanitization of query text."""
        return v.strip()

