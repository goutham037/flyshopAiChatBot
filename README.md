# FlyShop AI ChatBot - MVP Query API

A secure, read-only natural language query API for FlyShop CRM customers to access their travel bookings, payments, and quotations.

## Features

- **Natural Language Processing**: Uses Gemini LLM for intent and entity extraction
- **Mobile-Scoped Security**: All queries filtered by customer's registered mobile number
- **SQL Template Engine**: Pre-defined safe SQL templates with parameter binding
- **11 Supported Intents**: Bookings, payments, quotations, activities, and more

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and update:

```bash
cp .env.example .env
```

Required settings:

- `DATABASE_URL`: MySQL connection string for read-only user
- `GEMINI_API_KEY`: Your Gemini API key

### 3. Run the Server

```bash
uvicorn app.main:app --reload --port 8000
```

### 4. Try It Out

Open <http://localhost:8000/docs> for the Swagger UI.

Example request:

```bash
curl -X POST http://localhost:8000/mvp/query \
  -H "Content-Type: application/json" \
  -d '{
    "mobile": "+919999999999",
    "query": "Show my booking for FS1234"
  }'
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/mvp/query` | POST | Natural language query |
| `/health` | GET | Health check |
| `/intents` | GET | List supported intents |
| `/docs` | GET | Swagger UI |

## Supported Intents

- `booking_status` - Flight booking confirmation
- `list_bookings` - List all bookings
- `quotation_detail` - Quotation details
- `list_quotations` - List all quotations
- `payment_status` - Payment status for a query
- `list_payments` - List all payments
- `payment_schedule` - Scheduled payments
- `activity_status` - Activity booking status
- `admin_info` - Admin contact info
- `message_history` - WhatsApp message history
- `query_summary` - Consolidated query view

## Project Structure

```
app/
├── main.py              # FastAPI application
├── config.py            # Environment configuration
├── api/
│   └── query.py         # POST /mvp/query endpoint
├── core/
│   ├── intent_extractor.py   # LLM-based extraction
│   ├── query_planner.py      # Template selection
│   ├── schema_mapper.py      # Exposed columns
│   ├── sql_templates.py      # SQL templates
│   ├── sql_validator.py      # Safety validation
│   └── response_formatter.py # Response formatting
├── db/
│   └── database.py      # Async MySQL connection
└── models/
    ├── requests.py      # Request models
    └── responses.py     # Response models
```

## Security

- **Read-only DB user**: Only SELECT privileges
- **Parameter binding**: No SQL string interpolation
- **Blocked keywords**: INSERT, UPDATE, DELETE, DROP, etc.
- **Mobile scoping**: All queries filtered by user mobile
- **PII masking**: Mobile numbers masked in logs
