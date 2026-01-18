"""
SQL Template Catalog: Pre-defined SQL templates for each supported intent.
All templates use parameter binding - no string interpolation.
Updated to use real database table names (snake_case).
"""
from typing import Optional
from app.models.responses import Intent


# SQL Templates mapped by intent
# All queries enforce mobile-scoping via JOIN to query_masters
# Table names match the real database schema (snake_case)
SQL_TEMPLATES: dict[str, dict] = {
    Intent.BOOKING_STATUS: {
        "description": "Get booking confirmation & flight details",
        "required_entities": ["query_id"],
        "optional_entities": [],
        "query": """
            SELECT 
                qf.query_id, qf.pnr, qf.is_roundtrip,
                qf.flight_number, qf.airline, qf.airline_code,
                qf.from_location, qf.to_location,
                qf.departure_datetime, qf.arrival_datetime,
                qf.number_of_stops,
                qf.return_flight_number, qf.return_departure_datetime, qf.return_arrival_datetime,
                qf.adult_price, qf.child_price, qf.infant_price
            FROM query_flight_manages qf
            JOIN query_masters qm ON qf.query_id = qm.query_id
            WHERE qm.user_mobile = :mobile
              AND qf.query_id = :query_id
            LIMIT 1
        """,
        "sanitized": "SELECT qf.* FROM query_flight_manages qf JOIN query_masters qm ON ... WHERE qm.user_mobile = ? AND qf.query_id = ?"
    },
    
    Intent.LIST_BOOKINGS: {
        "description": "List all bookings for user",
        "required_entities": [],
        "optional_entities": ["status"],
        "query": """
            SELECT 
                qf.query_id, qf.pnr, qf.is_roundtrip,
                qf.flight_number, qf.airline,
                qf.from_location, qf.to_location,
                qf.departure_datetime, qf.arrival_datetime
            FROM query_flight_manages qf
            JOIN query_masters qm ON qf.query_id = qm.query_id
            WHERE qm.user_mobile = :mobile
            ORDER BY qf.departure_datetime DESC
            LIMIT :limit OFFSET :offset
        """,
        "sanitized": "SELECT qf.* FROM query_flight_manages qf JOIN query_masters qm ON ... WHERE qm.user_mobile = ? LIMIT ? OFFSET ?"
    },
    
    # List all queries/travel requests for user (for "my details" / "my profile" requests)
    "my_profile": {
        "description": "Get comprehensive user profile with data from all tables",
        "required_entities": [],
        "optional_entities": [],
        "query": """
            SELECT 
                qm.user_name, qm.user_mobile, qm.user_email,
                -- Stats
                COUNT(DISTINCT qm.query_id) as total_trips_planned,
                -- Payment Summary (Total across all queries)
                (SELECT SUM(recieved_amount) FROM query_payments qp JOIN query_masters qm2 ON qp.query_id = qm2.query_id WHERE qm2.user_mobile = :mobile) as total_spent,
                -- Recent Queries (concatenated)
                (SELECT GROUP_CONCAT(CONCAT('#', query_id, ' ', destination_name, ' (', DATE_FORMAT(created_at, '%Y-%m-%d'), ')') SEPARATOR ' | ') 
                 FROM (SELECT * FROM query_masters WHERE user_mobile = :mobile ORDER BY created_at DESC LIMIT 5) as sub_q) as recent_queries,
                -- Recent Bookings
                (SELECT GROUP_CONCAT(CONCAT(airline, ' ', flight_number, ' ', from_location, '-', to_location) SEPARATOR ' | ') 
                 FROM (SELECT qf.* FROM query_flight_manages qf JOIN query_masters qm3 ON qf.query_id = qm3.query_id WHERE qm3.user_mobile = :mobile ORDER BY departure_datetime DESC LIMIT 5) as sub_f) as recent_flights
            FROM query_masters qm
            WHERE qm.user_mobile = :mobile
            GROUP BY qm.user_mobile 
            LIMIT 1
        """,
        "sanitized": "SELECT user_name, total_trips, total_spent... FROM query_masters WHERE user_mobile = ?"
    },
    
    # List all queries/travel requests for user
    Intent.LIST_QUERIES: {
        "description": "List all travel queries/requests for user",
        "required_entities": [],
        "optional_entities": [],
        "query": """
            SELECT 
                qm.query_id, qm.user_name, qm.user_email, qm.user_mobile,
                qm.destination_name, qm.from_date, qm.to_date,
                qm.adult, qm.child, qm.infant,
                qm.query_stage, qm.service_name, qm.priority,
                qm.created_at
            FROM query_masters qm
            WHERE qm.user_mobile = :mobile
            ORDER BY qm.created_at DESC
            LIMIT :limit OFFSET :offset
        """,
        "sanitized": "SELECT qm.* FROM query_masters qm WHERE qm.user_mobile = ? LIMIT ? OFFSET ?"
    },
    
    Intent.QUOTATION_DETAIL: {
        "description": "Get quotation details",
        "required_entities": ["query_id"],
        "optional_entities": ["quotation_id"],
        "query": """
            SELECT 
                qq.quotation_id, qq.query_id, qq.price, qq.supplier_price,
                qq.currency, qq.status, qq.query_type, qq.sent_at, qq.confirm_at
            FROM query_quotations qq
            JOIN query_masters qm ON qq.query_id = qm.query_id
            WHERE qm.user_mobile = :mobile
              AND qq.query_id = :query_id
            ORDER BY qq.sent_at DESC
            LIMIT :limit
        """,
        "sanitized": "SELECT qq.* FROM query_quotations qq JOIN query_masters qm ON ... WHERE qm.user_mobile = ? AND qq.query_id = ?"
    },
    
    Intent.LIST_QUOTATIONS: {
        "description": "List all quotations for user",
        "required_entities": [],
        "optional_entities": ["query_id"],
        "query": """
            SELECT 
                qq.quotation_id, qq.query_id, qq.price, qq.currency,
                qq.status, qq.sent_at, qq.confirm_at
            FROM query_quotations qq
            JOIN query_masters qm ON qq.query_id = qm.query_id
            WHERE qm.user_mobile = :mobile
            ORDER BY qq.sent_at DESC
            LIMIT :limit OFFSET :offset
        """,
        "sanitized": "SELECT qq.* FROM query_quotations qq JOIN query_masters qm ON ... WHERE qm.user_mobile = ?"
    },
    
    Intent.PAYMENT_STATUS: {
        "description": "Get payment details for a query",
        "required_entities": ["query_id"],
        "optional_entities": [],
        "query": """
            SELECT 
                qp.query_id, qp.quotation_id, qp.net_amount, qp.total_amount,
                qp.recieved_amount, qp.pending_amount, qp.grand_total_amount,
                qp.cgst, qp.sgst, qp.igst, qp.discount, qp.discount_name,
                qp.gross_profit, qp.supplier_amount
            FROM query_payments qp
            JOIN query_masters qm ON qp.query_id = qm.query_id
            WHERE qm.user_mobile = :mobile
              AND qp.query_id = :query_id
            LIMIT 1
        """,
        "sanitized": "SELECT qp.* FROM query_payments qp JOIN query_masters qm ON ... WHERE qm.user_mobile = ? AND qp.query_id = ?"
    },
    
    Intent.LIST_PAYMENTS: {
        "description": "List all payments for user",
        "required_entities": [],
        "optional_entities": ["status"],
        "query": """
            SELECT 
                qp.query_id, qp.pending_amount, qp.recieved_amount,
                qp.total_amount, qp.grand_total_amount, qp.discount
            FROM query_payments qp
            JOIN query_masters qm ON qp.query_id = qm.query_id
            WHERE qm.user_mobile = :mobile
            ORDER BY qp.id DESC
            LIMIT :limit OFFSET :offset
        """,
        "sanitized": "SELECT qp.* FROM query_payments qp JOIN query_masters qm ON ... WHERE qm.user_mobile = ?"
    },
    
    Intent.PAYMENT_SCHEDULE: {
        "description": "Get scheduled payments for a query",
        "required_entities": ["query_id"],
        "optional_entities": [],
        "query": """
            SELECT 
                ps.payment_id, ps.query_id, ps.amount, ps.payment_type,
                ps.status, ps.payment_link, ps.payment_link_sent_at,
                ps.payment_date, ps.payment_time, ps.payment_receipt,
                ps.gateway_name, ps.transaction_id
            FROM query_payment_schedulers ps
            JOIN query_masters qm ON ps.query_id = qm.query_id
            WHERE qm.user_mobile = :mobile
              AND ps.query_id = :query_id
            ORDER BY ps.payment_date ASC
        """,
        "sanitized": "SELECT ps.* FROM query_payment_schedulers ps JOIN query_masters qm ON ... WHERE qm.user_mobile = ? AND ps.query_id = ?"
    },
    
    Intent.ACTIVITY_STATUS: {
        "description": "Get activity booking details",
        "required_entities": ["query_id"],
        "optional_entities": ["activity_id"],
        "query": """
            SELECT 
                qa.activity_id, qa.query_id, qa.activity_option_id, qa.quotation_id,
                qa.date, qa.transfer_type, qa.destination,
                qa.adult_cost, qa.child_cost, qa.is_confirmed, qa.confirmed_date
            FROM query_activities qa
            JOIN query_masters qm ON qa.query_id = qm.query_id
            WHERE qm.user_mobile = :mobile
              AND qa.query_id = :query_id
            ORDER BY qa.date ASC
        """,
        "sanitized": "SELECT qa.* FROM query_activities qa JOIN query_masters qm ON ... WHERE qm.user_mobile = ? AND qa.query_id = ?"
    },
    
    Intent.ADMIN_INFO: {
        "description": "Get admin contact info for a query",
        "required_entities": ["query_id"],
        "optional_entities": [],
        "query": """
            SELECT 
                ma.name, ma.email, ma.phone, ma.user_type, ma.m_code
            FROM master_admins ma
            JOIN query_masters qm ON qm.assign_to = ma.m_code OR qm.admin_ref = ma.m_code
            WHERE qm.user_mobile = :mobile
              AND qm.query_id = :query_id
            LIMIT 1
        """,
        "sanitized": "SELECT ma.* FROM master_admins ma JOIN query_masters qm ON ... WHERE qm.user_mobile = ? AND qm.query_id = ?"
    },
    
    Intent.MESSAGE_HISTORY: {
        "description": "Get WhatsApp message history (table not yet created)",
        "required_entities": [],
        "optional_entities": ["query_id"],
        "query": """
            SELECT 'Message history table not yet available' as message
        """,
        "sanitized": "SELECT message FROM ... (table not available)"
    },
    
    Intent.QUERY_SUMMARY: {
        "description": "Consolidated view for a query",
        "required_entities": ["query_id"],
        "optional_entities": [],
        "query": """
            SELECT 
                qm.query_id, qm.user_name, qm.user_mobile, qm.user_email,
                qm.destination_name, qm.from_date, qm.to_date,
                qm.adult, qm.child, qm.infant,
                qm.query_stage, qm.service, qm.service_name,
                qm.lead_source, qm.priority,
                qq.quotation_id, qq.price, qq.currency, qq.status as quotation_status,
                qp.pending_amount, qp.recieved_amount, qp.total_amount,
                qf.pnr, qf.flight_number, qf.airline
            FROM query_masters qm
            LEFT JOIN query_quotations qq ON qm.query_id = qq.query_id
            LEFT JOIN query_payments qp ON qm.query_id = qp.query_id
            LEFT JOIN query_flight_manages qf ON qm.query_id = qf.query_id
            WHERE qm.user_mobile = :mobile
              AND qm.query_id = :query_id
            LIMIT 1
        """,
        "sanitized": "SELECT qm.*, qq.*, qp.*, qf.* FROM query_masters qm LEFT JOIN ... WHERE qm.user_mobile = ? AND qm.query_id = ?"
    }
}


def get_template(intent: str) -> Optional[dict]:
    """Get SQL template for an intent."""
    return SQL_TEMPLATES.get(intent)


def get_all_intents() -> list[str]:
    """Get list of all supported intents."""
    return list(SQL_TEMPLATES.keys())


def get_required_entities(intent: str) -> list[str]:
    """Get required entities for an intent."""
    template = SQL_TEMPLATES.get(intent)
    return template["required_entities"] if template else []
