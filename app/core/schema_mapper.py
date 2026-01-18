"""
Schema Mapper: Maps models to their exposed (safe) columns.
Only these columns can be returned to customers via the API.
"""
from typing import Set


# Exposed columns per model - curated subset safe for customer access
EXPOSED_COLUMNS: dict[str, Set[str]] = {
    "QueryMaster": {
        "query_id", "user_name", "user_email", "user_mobile",
        "destination_name", "from_date", "to_date", "travel_month",
        "adult", "child", "infant", "query_stage", "priority",
        "assign_to", "service", "remark", "lead_source"
    },
    
    "QueryQuotation": {
        "quotation_id", "query_id", "price", "supplier_price",
        "currency", "status", "query_type", "sent_at", "confirm_at"
    },
    
    "QueryFlightManage": {
        "quotation_id", "query_id", "from_location", "to_location",
        "flight_number", "airline", "airline_code",
        "departure_datetime", "arrival_datetime", "pnr",
        "number_of_stops", "onward_adult_price",
        "return_from_location", "return_to_location",
        "return_flight_number", "return_airline",
        "return_departure_datetime", "return_arrival_datetime",
        "is_roundtrip", "is_confirmed", "confirmed_date"
    },
    
    "QueryActivity": {
        "activity_id", "query_id", "activity_option_id",
        "date", "days", "transfer_type", "destination",
        "adult_cost", "child_cost", "is_confirmed", "confirmed_date"
    },
    
    "QueryActivityMarkup": {
        "query_id", "markup_type", "markup_value"
    },
    
    "QueryPayment": {
        "query_id", "quotation_id", "net_amount", "total_amount",
        "recieved_amount", "pending_amount", "grand_total_amount",
        "gross_profit", "supplier_amount", "supplier_recieved",
        "supplier_pending", "supplier_id", "cgst", "sgst", "igst",
        "tcs", "gst_on_markup", "markup_type", "markup_value",
        "discount", "discount_name"
    },
    
    "QueryPaymentScheduler": {
        "payment_id", "query_id", "payment_type", "amount",
        "payment_receipt", "status", "gateway_name", "payment_link",
        "payment_link_sent_at", "payment_date", "payment_time",
        "last_action_by"
    },
    
    "MasterAdmin": {
        "m_code", "name", "email", "phone", "user_type"
    },
    
    "MasterWhatsappMessage": {
        "message", "message_id", "message_type", "message_status",
        "jid", "is_image", "image_url", "is_document",
        "document_url", "created_at"
    },
    
    "User": {
        "name", "email", "user_mobile", "email_verified_at"
        # Note: password is NEVER exposed
    }
}

# Allowed table names for validation
ALLOWED_TABLES: Set[str] = set(EXPOSED_COLUMNS.keys())

# Allowed joins (fixed patterns for MVP)
ALLOWED_JOINS: list[tuple[str, str, str, str]] = [
    # (table1, table2, table1_col, table2_col)
    ("QueryMaster", "QueryQuotation", "query_id", "query_id"),
    ("QueryMaster", "QueryFlightManage", "query_id", "query_id"),
    ("QueryQuotation", "QueryPayment", "quotation_id", "quotation_id"),
    ("QueryMaster", "QueryPayment", "query_id", "query_id"),
    ("QueryMaster", "QueryPaymentScheduler", "query_id", "query_id"),
    ("QueryMaster", "MasterWhatsappMessage", "admin_ref", "admin_ref"),
    ("QueryMaster", "MasterAdmin", "admin_ref", "m_code"),
]


def get_exposed_columns(table_name: str) -> Set[str]:
    """Get exposed columns for a table."""
    return EXPOSED_COLUMNS.get(table_name, set())


def is_column_allowed(table_name: str, column_name: str) -> bool:
    """Check if a column is allowed for a given table."""
    columns = EXPOSED_COLUMNS.get(table_name, set())
    return column_name in columns


def is_table_allowed(table_name: str) -> bool:
    """Check if a table is allowed."""
    return table_name in ALLOWED_TABLES
