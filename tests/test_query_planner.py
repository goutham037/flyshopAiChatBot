"""
Tests for query planner.
"""
import pytest
from app.core.query_planner import create_query_plan, QueryPlan, QueryPlanError
from app.core.intent_extractor import IntentExtractionResult
from app.models.responses import ErrorCode


class TestCreateQueryPlan:
    """Tests for query plan creation."""
    
    def test_unknown_intent_returns_error(self):
        """Unknown intent should return error."""
        extraction = IntentExtractionResult(intent="unknown", entities={})
        result = create_query_plan(extraction, mobile="+919999999999")
        
        assert isinstance(result, QueryPlanError)
        assert result.error_code == ErrorCode.UNKNOWN_INTENT
    
    def test_missing_required_entity_returns_error(self):
        """Missing required entity should return error."""
        # booking_status requires query_id
        extraction = IntentExtractionResult(intent="booking_status", entities={})
        result = create_query_plan(extraction, mobile="+919999999999")
        
        assert isinstance(result, QueryPlanError)
        assert result.error_code == ErrorCode.AMBIGUOUS_ENTITY
    
    def test_valid_booking_status_returns_plan(self):
        """Valid booking status request should return QueryPlan."""
        extraction = IntentExtractionResult(
            intent="booking_status",
            entities={"query_id": "FS1234"}
        )
        result = create_query_plan(extraction, mobile="+919999999999")
        
        assert isinstance(result, QueryPlan)
        assert result.intent == "booking_status"
        assert result.params["mobile"] == "+919999999999"
        assert result.params["query_id"] == "FS1234"
        assert "SELECT" in result.sql
    
    def test_list_payments_no_required_entities(self):
        """list_payments should work without required entities."""
        extraction = IntentExtractionResult(intent="list_payments", entities={})
        result = create_query_plan(extraction, mobile="+919999999999")
        
        assert isinstance(result, QueryPlan)
        assert result.intent == "list_payments"
    
    def test_limit_and_offset_passed(self):
        """Limit and offset should be passed to params."""
        extraction = IntentExtractionResult(intent="list_payments", entities={})
        result = create_query_plan(
            extraction,
            mobile="+919999999999",
            limit=25,
            offset=10
        )
        
        assert isinstance(result, QueryPlan)
        assert result.params["limit"] == 25
        assert result.params["offset"] == 10
