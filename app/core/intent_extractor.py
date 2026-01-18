"""
Conversational AI Assistant: Uses Gemini 2.5-flash for natural language understanding.
Multilingual, context-aware, and truly conversational - answers ANY question.
Supports all CRM models and general helpdesk queries.
"""
import json
import logging
import asyncio
from typing import Optional
import google.generativeai as genai

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# Configure Gemini with direct API key
if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)
    logger.info("[startup] Gemini API configured with direct API key")
else:
    logger.warning("[startup] No GEMINI_API_KEY configured!")

# Initialize the model
MODEL_NAME = "gemini-2.5-flash"

def get_model():
    """Get the Gemini model instance."""
    return genai.GenerativeModel(
        model_name=MODEL_NAME,
        generation_config={
            "temperature": 0.4,
            "max_output_tokens": 2048,
        }
    )

# Supported intents for structured data queries
SUPPORTED_INTENTS = [
    # Query/Booking related
    "booking_status", "list_bookings", "query_summary", "list_queries",
    # Quotation related
    "quotation_detail", "list_quotations",
    # Payment related  
    "payment_status", "list_payments", "payment_schedule",
    # Activity/Package related
    "activity_status", "list_activities",
    # Admin/Support
    "admin_info", "message_history", "my_profile",
    # General conversation
    "general_help", "greeting", "unknown"
]

# Full CRM Database Schema for context
CRM_SCHEMA = """
## FlyShop CRM Database Models:

1. **QueryMaster** (query_masters) - Central travel query/lead
   - query_id, admin_ref, user_name, user_email, user_mobile
   - destination_name, from_date, to_date, travel_month
   - adult, child, infant, query_stage, priority, service_name, lead_source

2. **QueryQuotation** (query_quotations) - Price quotations
   - quotation_id, query_id, price, supplier_price, currency, status
   - sent_at, confirm_at

3. **QueryFlightManage** (query_flight_manages) - Flight bookings
   - query_id, quotation_id, pnr, flight_number, airline
   - from_location, to_location, departure_datetime, arrival_datetime
   - is_roundtrip, return flight details, prices

4. **QueryActivity** (query_activities) - Activity/package bookings
   - activity_id, query_id, date, destination, transfer_type
   - adult_cost, child_cost, is_confirmed

5. **QueryPayment** (query_payments) - Payment summary
   - query_id, total_amount, recieved_amount, pending_amount
   - taxes (cgst, sgst, igst), discount, supplier amounts

6. **QueryPaymentScheduler** (query_payment_schedulers) - Payment transactions
   - payment_id, query_id, amount, payment_type, status
   - payment_link, payment_date, gateway_name, transaction_id

7. **MasterAdmin** (master_admins) - Admin/Sales contacts
   - m_code, name, email, phone, user_type

8. **MasterWhatsappMessage** (master_whatsapp_messages) - Chat history
   - message, message_type, message_status, attachments
"""

# Comprehensive conversational system prompt
SYSTEM_PROMPT = f"""You are FlyShop's AI Travel Assistant - a helpful, friendly, multilingual chatbot.

## 1. LANGUAGE & TONE RULES (CRITICAL):
- **Detect Language**: Note the user's language (English, Telugu, Hindi, etc.) and ALWAYS reply in the SAME language.
- **Strict Adherence**: If user says "talk in Telugu only", OBEY until asked otherwise.
- **Tone**: Professional, polite, and direct. **NO EMOJIS**.
- **No Robot Speak**: Avoid dry, technical jargon. Be concise and helpful.
- **Safety**: If user sends flirty/emotional messages, politely redirect to travel assistance.

## 2. CONVERSATION MEMORY & CONTEXT:
- **Remember Context**: Track the last requested domain (payments, bookings) and the last list shown.
- **Reference Resolution**:
  - "that one", "adi", "idi", "first one", "1st", "number 2" → ALL refer to items in the PREVIOUS list/message.
  - "its payment", "dani payment" → Refers to the last discussed Booking/Query.
- **Name**: Use the user's name if known from history.

## DATABASE KNOWLEDGE:
{CRM_SCHEMA}

## 3. INTENT DETECTION GUIDE:

### A. DATA LOOKUPS (needs_data: true)
- **Payments**: "payment status", "pending amount", "transaction history" -> `payment_status` or `list_payments`
- **Quotations**: "show quote", "price details", "QT772898" -> `quotation_detail` or `list_quotations`
- **Bookings**: "my flights", "booking status", "PNR status" -> `booking_status` or `list_bookings`
- **Queries/Leads**: "travel requests", "my plans", "FS1234" -> `query_summary` or `list_queries`
- **Profile**: "who am i", "my details", "tell me about myself", "my profile" -> `my_profile`
- **Activities**: "tour status", "activity voucher" -> `activity_status`

### B. GENERAL / SUPPORT (needs_data: false)
- **Support**: "contact admin", "customer care", "whatsapp number", "ekkada contact cheyali" -> `admin_info`
- **Help**: "help me", "em cheyagalav", "madad karo" -> `general_help`
- **Greeting**: "hi", "namaste", "ela unnav" -> `greeting`

## 4. ENTITY & ID RECOGNITION RULES:
- **Query IDs**: FS1234, 433942, 817118
- **Quotation IDs**: QT772898, QT123456
- **Bare IDs**: "QT772898" -> quotation_detail. "817118" -> query_summary.
- **Ordinals/Indices**: "1st", "second", "1", "2" -> Interpret as selection from previous list.

## 5. SELECTION & AMBIGUITY HANDLING:
- **List Selection**: If user replies "1", "1st one", "adi" after a list -> Map to the SPECIFIC INTENT of that item. **Check conversation history to find the ID (e.g., QT772898)**.
- **Multiple Results**: If user has multiple records (e.g., 2 bookings), we will show a numbered list.
- **Clarification**: If ID is missing and context is unclear, set `clarification_needed: true` and ask politely: "I see a few options! Which trip or Query ID are you asking about?"

## RESPONSE FORMAT (JSON ONLY):
```json
{{
  "intent": "<one of: {', '.join(SUPPORTED_INTENTS)}>",
  "entities": {{
    "query_id": "<RESOLVE FROM CONTEXT IF POSSIBLE>",
    "quotation_id": "<RESOLVE FROM CONTEXT IF POSSIBLE>",
    "ordinal_selection": "<Fallback only: '1', '2', 'first'>"
  }},
  "response_language": "<detected: en, hi, te, ta, etc>",
  "needs_data": <true for CRM lookups, false for chat>,
  "missing_params": ["<list of required params if missing>"],
  "clarification_needed": <true if we strictly need ID to proceed>,
  "friendly_message": "<Warm, conversational response in user's language>"
}}
```

## EDGE CASE MAPPINGS:
1. **"1st dhi", "first one", "1"** (after list) → Intent: `quotation_detail` (or relevant type). **Infer ID from history**.
2. **"QT772898"** (bare ID) → Intent: `quotation_detail`, Entity: `quotation_id=QT772898`
3. **"flight tickets", "my bookings"** → `list_bookings`
4. **"payment status"** (no ID) → `list_payments` (Showing list is better than asking "Which ID?")
5. **"Thank you"** → `general_help` (polite closing)

## EXAMPLES:

**User: "1st dhi" (Context: History shows list: 1. QT772898 ...)**
```json
{{
  "intent": "quotation_detail",
  "entities": {{"quotation_id": "QT772898"}}, 
  "response_language": "te",
  "friendly_message": "Checking Quotation #QT772898. Please wait."
}}
```

**User: "QT772898"**
```json
{{
  "intent": "quotation_detail",
  "entities": {{"quotation_id": "QT772898"}}, 
  "response_language": "en",
  "friendly_message": "Checking details for Quotation #QT772898."
}}
```

**Contextual Selection (Telugu):**
Bot: "You have 2 quotations..."
User: "1st dhi"
```json
{{
  "intent": "quotation_detail",
  "entities": {{"quotation_id": "<infer from history/context>"}}, 
  "response_language": "te", 
  "missing_params": ["quotation_id"], 
  "clarification_needed": true, 
  "needs_data": false, 
  "friendly_message": "Okay! Checking the first quotation. Please confirm the ID if possible?"
}}
```
*Note: If you can't infer the exact ID from history, ask for clarification politely.*

**Hindi greeting:**
User: "नमस्ते"
```json
{{
  "intent": "greeting", "entities": {{}}, "response_language": "hi", "needs_data": false, "friendly_message": "नमस्ते! FlyShop में आपका स्वागत है! आज मैं आपकी क्या मदद कर सकता हूं?"
}}
```

**General question (no data needed):**
User: "How do I book a flight?"
```json
{{
  "intent": "general_help", "entities": {{"destination": "Goa"}}, "response_language": "en", "needs_data": false, "friendly_message": "Great question! Here's how you can book a flight with FlyShop:\n\n1. Share your travel dates and destination\n2. We'll send you the best flight options\n3. Choose your preferred flight\n4. Make the payment\n5. Get your confirmed PNR!\n\nWant me to help you start a booking?"
}}
```

**Data lookup (needs data):**
User: "Show my bookings"
```json
{{
  "intent": "list_bookings", "entities": {{}}, "response_language": "en", "needs_data": true, "friendly_message": "Let me fetch all your flight bookings!"
}}
```

**Hindi data request:**
User: "मेरी payment कितनी pending है?"
```json
{{
  "intent": "list_payments", "entities": {{}}, "response_language": "hinglish", "needs_data": true, "friendly_message": "आपकी pending payments चेक करता हूं!"
}}
```

**Specific query:**
User: "817118 का status बताओ"
```json
{{
  "intent": "query_summary", "entities": {{"query_id": "817118"}}, "response_language": "hinglish", "needs_data": true, "friendly_message": "Query 817118 की पूरी details निकालता हूं!"
}}
```

**Follow-up with context:**
User: "और इसकी payment?" (previous context was about query 817118)
```json
{{
  "intent": "payment_status", "entities": {{"query_id": "817118"}}, "response_language": "hinglish", "needs_data": true, "friendly_message": "Query 817118 की payment details देखता हूं!"
}}
```

**Travel question:**
User: "Best time to visit Goa?"
```json
{{
  "intent": "general_help", "entities": {{"destination": "Goa"}}, "response_language": "en", "needs_data": false, "friendly_message": "Great choice! Goa is amazing!\n\n**Best time to visit:**\n- Nov to Feb: Perfect weather, peak season\n- Oct & Mar: Good weather, fewer crowds\n- Monsoon (Jun-Sep): Lush green, budget-friendly\n\nWould you like me to help you plan a trip to Goa?"
}}
```
"""


class IntentExtractionResult:
    """Result of intent extraction with support for clarification and missing params."""
    def __init__(self, intent: str, entities: dict, confidence: float = 1.0, 
                 response_language: str = "en", friendly_message: str = "",
                 needs_data: bool = True, missing_params: list = None,
                 clarification_needed: bool = False):
        self.intent = intent
        self.entities = entities
        self.confidence = confidence
        self.response_language = response_language
        self.friendly_message = friendly_message
        self.needs_data = needs_data
        self.missing_params = missing_params or []
        self.clarification_needed = clarification_needed
    
    def is_unknown(self) -> bool:
        return self.intent == "unknown"
    
    def is_general_chat(self) -> bool:
        """Check if this is a general chat that doesn't need database."""
        return not self.needs_data or self.intent in ["greeting", "general_help"]
    
    def needs_clarification(self) -> bool:
        """Check if we need to ask user for more information."""
        return self.clarification_needed or len(self.missing_params) > 0


async def extract_intent_and_entities(query: str, conversation_context: Optional[str] = None, preferred_language: Optional[str] = None) -> IntentExtractionResult:
    """
    Extract intent and entities from a natural language query using Gemini.
    Multilingual and context-aware - understands Hindi, English, Hinglish, etc.
    Can answer ANY type of question - both data lookups and general chat.
    
    Args:
        query: User's natural language query
        conversation_context: Optional conversation history for context
        preferred_language: Optional language preference ('en', 'hi', 'hinglish'). 
                           If set, all responses will be in this language.
    """
    if not settings.GEMINI_API_KEY:
        logger.error("Gemini API key not configured")
        return IntentExtractionResult(intent="unknown", entities={}, friendly_message="API not configured")

    try:
        model = get_model()
        
        # Build the full prompt with context
        context_section = ""
        if conversation_context:
            context_section = f"""
## CONVERSATION HISTORY:
{conversation_context}

(Use this to understand what "that", "this", "it", "इसी", "वो", "उसका" etc. refer to. Extract entity values from context if user doesn't repeat them.)
"""
        
        # Add language enforcement if preferred_language is set
        language_instruction = ""
        if preferred_language:
            lang_name = {
                "en": "English",
                "hi": "Hindi (हिंदी)",
                "hinglish": "Hinglish (mix of Hindi and English)"
            }.get(preferred_language, "English")
            language_instruction = f"""
## IMPORTANT - LANGUAGE REQUIREMENT:
The user has set their preferred language to: **{lang_name}**
You MUST respond ONLY in {lang_name}. Do NOT switch to any other language.
Set response_language to "{preferred_language}" in your JSON response.
"""
        
        full_prompt = f"""{SYSTEM_PROMPT}

{language_instruction}
{context_section}

## CURRENT USER MESSAGE:
{query}

## YOUR JSON RESPONSE:"""
        
        # Generate response asynchronously
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None,
            lambda: model.generate_content(full_prompt)
        )
        
        # Parse the response
        response_text = response.text.strip() if response.text else "{}"
        logger.info(f"GEMINI RAW RESPONSE:\n{response_text}\n-------------------")
        
        # Clean up common JSON formatting issues
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        # Try to extract JSON from response if it contains other text
        import re
        json_match = re.search(r'\{[^{}]*\}', response_text, re.DOTALL)
        if json_match and not response_text.startswith('{'):
            response_text = json_match.group(0)
        
        # Fix common JSON issues: single quotes to double quotes (but not inside strings)
        # Replace 'key': with "key":
        response_text = re.sub(r"'(\w+)'(\s*:)", r'"\1"\2', response_text)
        # Replace : 'value' with : "value" (for simple string values)
        response_text = re.sub(r":\s*'([^']*)'", r': "\1"', response_text)
        # Fix True/False to true/false
        response_text = response_text.replace(': True', ': true').replace(': False', ': false')
        response_text = response_text.replace(':True', ':true').replace(':False', ':false')
        # Remove trailing commas before } or ]
        response_text = re.sub(r',\s*}', '}', response_text)
        response_text = re.sub(r',\s*]', ']', response_text)
        
        # Parse JSON
        data = json.loads(response_text)
        
        intent = data.get("intent", "unknown")
        entities = data.get("entities", {})
        response_language = data.get("response_language", "en")
        friendly_message = data.get("friendly_message", "")
        needs_data = data.get("needs_data", True)
        missing_params = data.get("missing_params", [])
        clarification_needed = data.get("clarification_needed", False)
        
        # Validate intent
        if intent not in SUPPORTED_INTENTS:
            # For unrecognized intents, treat as general_help
            intent = "general_help"
            needs_data = False
        
        # Clean up empty entities
        entities = {k: v for k, v in entities.items() if v}
        
        # Clean up missing_params (remove empty strings)
        if isinstance(missing_params, list):
            missing_params = [p for p in missing_params if p and p.strip()]
        else:
            missing_params = []
        
        logger.info(f"Gemini: intent={intent}, lang={response_language}, needs_data={needs_data}, clarify={clarification_needed}, entities={list(entities.keys())}")
        
        return IntentExtractionResult(
            intent=intent, 
            entities=entities,
            response_language=response_language,
            friendly_message=friendly_message,
            needs_data=needs_data,
            missing_params=missing_params,
            clarification_needed=clarification_needed
        )
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Gemini response as JSON: {e}")
        # Smart fallback: try to infer intent from query keywords
        query_lower = query.lower()
        
        # Check for data-related keywords in any language
        data_keywords = [
            'booking', 'payment', 'quotation', 'query', 'status', 'details', 'show', 'list',
            'my', 'mera', 'meri', 'naa', 'na', 'meri', 'mere',  # Hindi/Telugu possessives
            'చూపించు', 'వివరాలు', 'బుకింగ్',  # Telugu
            'दिखाओ', 'बुकिंग', 'पेमेंट',  # Hindi
        ]
        
        needs_data = any(kw in query_lower for kw in data_keywords)
        
        if needs_data:
            logger.info("Fallback: Detected data request from keywords, using list_queries")
            return IntentExtractionResult(
                intent="list_queries", 
                entities={},
                needs_data=True,
                friendly_message="Let me look up your information! 🔍"
            )
        else:
            return IntentExtractionResult(
                intent="general_help", 
                entities={},
                needs_data=False,
                friendly_message="Hmm, I didn't quite catch that 😊 Were you asking about:\n• 💳 Payments\n• 📝 Quotations\n• ✈️ Bookings\n• 📋 Your travel queries\n\nJust let me know and I'll help!"
            )
    except Exception as e:
        logger.error(f"Intent extraction failed: {e}")
        return IntentExtractionResult(
            intent="general_help", 
            entities={},
            needs_data=False,
            friendly_message="Oops, something went wrong on my end 😅 Could you try again? I'm here to help with payments, quotations, bookings, and more!"
        )


# Summary generation prompt - also multilingual
SUMMARY_PROMPT_TEMPLATE = """You are FlyShop's premium travel concierge. 
Your goal is to provide clear, professional, and elegant summaries.

## TASK:
Summarize the following travel data.
Respond in {language}.

## DATA TYPE: {intent}
## DATA:
{data}

## RESPONSE STYLE GUIDELINES (CRITICAL):
1. **Professional & Clean**: Use a polite, high-end agency tone. **NO EMOJIS**.
2. **"Attractive" Formatting**: 
   - Use **Bold** for key numbers (Amounts, IDs).
   - Use strictly aligned bullet points.
   - Keep it visually spacious and easy to read.
3. **Content Focus**:
   - For payments: Show amount, status (paid/pending), date.
   - For quotations: Show quotation ID, price, status (confirmed/pending).
   - For bookings: Show flight details, dates, destinations.
   - For admin info: Show Agent Name, formatted Email, and Phone. **Hide internal codes (user_type, m_code)**.
4. **Currency**: Use ₹ for amounts and format clearly (e.g., ₹50,000).
5. **Concise**: Get straight to the point. No fluff.

## EXAMPLE GOOD RESPONSE:
"Your payment of **₹50,000** for the Dubai trip (Query #433942) has been fully received. There is no pending balance.

**Quotations Found:**
• **QT772898**: ₹45,000 | Status: Confirmed
• **QT616045**: ₹38,000 | Status: Pending

Please let me know if you would like to proceed with the confirmed option."

## YOUR SUMMARY:"""


async def generate_summary(intent: str, data: list[dict], language: str = "en") -> Optional[str]:
    """Generate a human-friendly summary of the query results in the appropriate language."""
    if not data or not settings.GEMINI_API_KEY:
        return None
    
    try:
        model = get_model()
        limited_data = data[:5] if len(data) > 5 else data
        
        # Determine language label for prompt
        lang_label = {
            "hi": "Hindi",
            "hinglish": "Hinglish (mix of Hindi and English)",
            "te": "Telugu",
            "ta": "Tamil",
            "en": "English"
        }.get(language, "English")
        
        # Special handling for multiple results - ask user to select
        if len(data) > 1 and intent in ["query_summary", "payment_status", "booking_status", "quotation_detail", "activity_status"]:
            prompt = f"""You are FlyShop's professional travel assistant.
The user has multiple records. Help them choose one efficiently.

## DATA TYPE: {intent}
## RECORDS FOUND: {len(data)}
## DATA:
{json.dumps(limited_data, default=str)}

Generate a clean, professional response in {lang_label} that:
1. States clearly: "You have {len(data)} records."
2. Lists them using a numbered list:
   - 1. Query #ID - Destination (Dates)
   - 2. ...
3. Asks: "Please select one by number or ID."

**NO EMOJIS**. Keep it minimal and readable."""
        
        # Special handling for query selection fallback
        elif intent == "list_queries_for_selection":
            prompt = f"""You are FlyShop's professional travel assistant.
The user asked for info but didn't specify which trip.

Here are their recent travel queries:
{json.dumps(limited_data, default=str)}

Generate a polite clarification request in {lang_label}:
1. "I found a few trips under your account."
2. List them with IDs clearly (e.g. 1. Query #817118 - Dubai)
3. Ask: "Which one would you like to view?"

**NO EMOJIS**. Keep it professional."""
        # Special handling for user profile summary
        # Special handling for user profile summary
        elif intent == "my_profile":
            prompt = f"""You are FlyShop's professional travel assistant.
The user wants a complete profile report.

## COMPREHENSIVE USER DATA:
{json.dumps(limited_data, default=str)}

Generate a detailed, professional Profile Report in {lang_label}.
Format Requirements:
1. **Header**: "Travel Profile for [Name]"
2. **Account Overview**:
   - Total Trips Planned: [Count]
   - Total Spend with us: [Amount] (Format as ₹)
3. **Recent Activity**:
   - Parse the 'recent_queries' list (formatted as 'ID Name Date') and show the top 3 items cleanly.
   - Parse the 'recent_flights' list (formatted as 'Airline Number Route') and show the top 3 items cleanly.
4. **Closing**: "Thank you for choosing FlyShop. We look forward to your next journey."

**NO EMOJIS**. Use bold headers and clean lists."""
        
        else:
            prompt = SUMMARY_PROMPT_TEMPLATE.format(
                language=lang_label,
                intent=intent,
                data=json.dumps(limited_data, default=str)
            )
        
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None,
            lambda: model.generate_content(prompt)
        )
        
        response_text = response.text.strip() if response.text else ""
        logger.info(f"GEMINI SUMMARY RESPONSE:\n{response_text}\n-------------------")
        
        return response_text
        
    except Exception as e:
        logger.error(f"Summary generation failed: {e}")
        return None


async def generate_selection_list(data: list[dict], intent: str, language: str = "en") -> str:
    """Generate a numbered list for user to select from multiple results."""
    if not data or len(data) <= 1:
        return None
    
    return await generate_summary(intent, data, language)
