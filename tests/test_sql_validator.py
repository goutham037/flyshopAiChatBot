"""
Tests for SQL validator.
"""
import pytest
from app.core.sql_validator import (
    validate_sql_template,
    validate_parameters,
    sanitize_sql_for_display,
    SQLValidationError
)


class TestValidateSQLTemplate:
    """Tests for SQL template validation."""
    
    def test_valid_select_query(self):
        """Valid SELECT query should pass."""
        sql = "SELECT id, name FROM users WHERE id = :id"
        assert validate_sql_template(sql) is True
    
    def test_insert_blocked(self):
        """INSERT should be blocked."""
        sql = "INSERT INTO users (name) VALUES ('test')"
        with pytest.raises(SQLValidationError) as exc:
            validate_sql_template(sql)
        assert "INSERT" in str(exc.value)
    
    def test_update_blocked(self):
        """UPDATE should be blocked."""
        sql = "UPDATE users SET name = 'test'"
        with pytest.raises(SQLValidationError) as exc:
            validate_sql_template(sql)
        assert "UPDATE" in str(exc.value)
    
    def test_delete_blocked(self):
        """DELETE should be blocked."""
        sql = "DELETE FROM users"
        with pytest.raises(SQLValidationError) as exc:
            validate_sql_template(sql)
        assert "DELETE" in str(exc.value)
    
    def test_drop_blocked(self):
        """DROP should be blocked."""
        sql = "DROP TABLE users"
        with pytest.raises(SQLValidationError) as exc:
            validate_sql_template(sql)
        assert "DROP" in str(exc.value)
    
    def test_multi_statement_blocked(self):
        """Multiple statements should be blocked."""
        sql = "SELECT * FROM users; DROP TABLE users"
        with pytest.raises(SQLValidationError):
            validate_sql_template(sql)


class TestValidateParameters:
    """Tests for parameter validation."""
    
    def test_valid_params(self):
        """Valid parameters should pass."""
        params = {"mobile": "+919999999999", "limit": 50, "offset": 0}
        result = validate_parameters(params)
        assert result["mobile"] == "+919999999999"
        assert result["limit"] == 50
    
    def test_limit_capped(self):
        """Limit should be capped at MAX_LIMIT."""
        params = {"limit": 1000}
        result = validate_parameters(params)
        assert result["limit"] <= 500  # MAX_LIMIT
    
    def test_offset_non_negative(self):
        """Offset should not be negative."""
        params = {"offset": -10}
        result = validate_parameters(params)
        assert result["offset"] == 0
    
    def test_sql_comment_blocked(self):
        """SQL comments in values should be blocked."""
        params = {"query_id": "FS1234 --"}
        with pytest.raises(SQLValidationError):
            validate_parameters(params)


class TestSanitizeSQL:
    """Tests for SQL sanitization."""
    
    def test_replaces_named_params(self):
        """Named parameters should be replaced with ?."""
        sql = "SELECT * FROM users WHERE id = :id AND mobile = :mobile"
        result = sanitize_sql_for_display(sql)
        assert ":id" not in result
        assert ":mobile" not in result
        assert "?" in result
    
    def test_normalizes_whitespace(self):
        """Whitespace should be normalized."""
        sql = "SELECT  *   FROM   users"
        result = sanitize_sql_for_display(sql)
        assert "  " not in result
