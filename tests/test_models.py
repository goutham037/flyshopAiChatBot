"""
Tests for request models.
"""
import pytest
from pydantic import ValidationError
from app.models.requests import QueryRequest


class TestQueryRequest:
    """Tests for QueryRequest model validation."""
    
    def test_valid_request(self):
        """Valid request should pass."""
        request = QueryRequest(
            mobile="+919999999999",
            query="Show my booking"
        )
        assert request.mobile == "+919999999999"
        assert request.query == "Show my booking"
        assert request.limit == 50  # default
        assert request.offset == 0  # default
    
    def test_mobile_format_validation(self):
        """Invalid mobile format should fail."""
        with pytest.raises(ValidationError):
            QueryRequest(mobile="9999999999", query="test")
    
    def test_mobile_with_spaces(self):
        """Mobile with spaces should be normalized."""
        request = QueryRequest(
            mobile="+91 9999 999999",
            query="test query"
        )
        assert request.mobile == "+919999999999"
    
    def test_short_mobile_fails(self):
        """Mobile with wrong digit count should fail."""
        with pytest.raises(ValidationError):
            QueryRequest(mobile="+91999999", query="test")
    
    def test_query_too_short_fails(self):
        """Query shorter than 3 chars should fail."""
        with pytest.raises(ValidationError):
            QueryRequest(mobile="+919999999999", query="ab")
    
    def test_limit_range(self):
        """Limit must be between 1 and 500."""
        with pytest.raises(ValidationError):
            QueryRequest(mobile="+919999999999", query="test", limit=0)
        
        with pytest.raises(ValidationError):
            QueryRequest(mobile="+919999999999", query="test", limit=501)
    
    def test_offset_non_negative(self):
        """Offset must be non-negative."""
        with pytest.raises(ValidationError):
            QueryRequest(mobile="+919999999999", query="test", offset=-1)
