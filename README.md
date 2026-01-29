# FlyShop AI Chatbot (MVP)

A context-aware AI travel assistant built with **FastAPI**, **Google Gemini**, and **PostgreSQL/MySQL**. It provides a dual-interface for Customers (User Mode) and Administrators (Admin Mode), featuring real-time database RAG (Retrieval-Augmented Generation) and global analytics.

## 🚀 Features

### 👤 User Mode

- **Personalized Assistance**: Answers questions based on the user's *specific* booking history, payments, and quotations.
- **Privacy First**: Sensitive internal data (profits, supplier prices) is strictly filtered out.
- **Natural Language Querying**: "Show my payment schedule", "Is my Dubai flight confirmed?"

### 👮 Admin Mode (Inspector)

- **User Inspector**: Search and select any customer to view their full profile and data context.
- **Financial Visibility**: Admins see profit margins, supplier costs, and markup details that are hidden from users.
- **AI Analyst**: Ask business-level questions like "What is the profit margin for this booking?"

### 🌍 Global Analytics

- **"All Users" Context**: Admin can switch to a global view to analyze trends across the entire database.
- **Aggregated Stats**: Instant calculation of Total Revenue, Total Pending Payments, and Query volume.
- **Senior Analyst Persona**: The AI adapts to answer high-level business questions.

---

## 🛠️ Installation & Setup

### Prerequisites

- Python 3.9+
- Database (PostgreSQL or MySQL) with FlyShop schema
- Google Gemini API Key

### 1. Clone the Repository

```bash
git clone <repository-url>
cd flyshopAiChatBot
```

### 2. Create Virtual Environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configuration

Create a `.env` file in the root directory:

```ini
# Core
GEMINI_API_KEY=your_gemini_api_key_here
USE_MOCK_DATA=False

# Database
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_NAME=your_db_name
```

---

## ▶️ Running the Application

Start the backend server using Uvicorn:

```bash
uvicorn app.main:app --reload --port 8000
```

The server will start at `http://127.0.0.1:8000`.

---

## 📖 Usage Guide

1. **Open the Interface**: Go to `http://127.0.0.1:8000` in your browser.
2. **Select Mode**:
    - **User Mode**: Select a user mobile number to start chatting as that customer.
    - **Admin Mode**:
        - Select yourself as the **Admin**.
        - Select a **Client** to inspect OR select **"🌍 ALL USERS"** for global stats.
3. **Ask Questions**:
    - *User*: "Send me my voucher."
    - *Admin (Inspector)*: "Why is the Pending Amount so high for this user?"
    - *Admin (Global)*: "What is our total revenue today?"

---

## 📚 API Documentation

Interactive API docs are available at:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## 🛡️ Security Note

Data sanitization is handled server-side in `app/api/query.py`. The `sanitize_for_user_mode` function ensures that field-level security is enforced before data ever reaches the LLM or the frontend in User Mode.
