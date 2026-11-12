# FinAssist - Finance Loan Management AI Chatbot Web Application

FinAssist is a complete full-stack loan management and customer tracking web application designed specifically for small finance businesses. It automates financial calculations (Flat Interest and Reducing Balance EMI), repayment schedule generation, payment logging, customer CRM, analytics reporting with Chart.js, and includes an intelligent AI Chatbot powered by OpenAI API.

---

## Features

1. **Executive Dashboard**: Real-time stats for Total Customers, Active Loans, Amount Lent, Amount Repaid, Outstanding Balance, Expected Interest, and Today's Collections.
2. **AI Finance Chatbot**: Ask natural language questions ("How much does Ravi owe?", "Calculate ₹50,000 for 12 months at 2% interest", "Show today's collections"). Uses backend calculation engine and database queries with ZERO financial data hallucination.
3. **Dedicated Loan Calculator**: Side-by-side Flat vs. Reducing Balance interest comparisons, payment frequency adjustments (Daily, Weekly, Monthly), and full schedule breakdown table.
4. **Repayment Schedule Generator**: Automatic generation of per-installment principal, interest, due date, amount paid, and status (`Pending`, `Paid`, `Partially Paid`, `Overdue`).
5. **Customer Management**: Add, edit, delete, search, and view detailed borrowing history and outstanding balances.
6. **Loan Management**: Issue loans, track progress, view repayment schedules, and delete contracts.
7. **Payment Log**: Record payments in Cash, UPI, Bank Transfer, with automatic schedule allocation and loan balance update.
8. **Reports & Analytics**: Visual charts powered by Chart.js (Monthly Collections Trend, Loan Portfolio Status Split) and instant CSV Export.

---

## Technology Stack

- **Frontend**: HTML5, CSS3 (Vanilla Executive Dark Theme Design System), JavaScript (ES6 Modules)
- **Backend**: Python Flask, Flask-CORS
- **Database**: SQLite (`finance.db`)
- **AI Chatbot**: OpenAI API (`gpt-4o-mini` with tool use) & Fallback Engine
- **Charts**: Chart.js
- **Environment Configuration**: python-dotenv

---

## Local Installation & Setup Instructions (Windows)

Follow these exact steps to run FinAssist on your Windows laptop:

### 1. Open Terminal / PowerShell in Project Directory
```powershell
cd "e:\New folder"
```

### 2. Create Virtual Environment
```powershell
python -m venv venv
```

### 3. Activate Virtual Environment
```powershell
venv\Scripts\activate
```

### 4. Install Requirements
```powershell
python -m pip install -r backend\requirements.txt
```

### 5. Configure Environment Variables (`.env`)
Create or edit `.env` in the root folder:
```env
OPENAI_API_KEY=your_openai_api_key_here
FLASK_PORT=5000
SECRET_KEY=finassist_super_secret_key_2026
```
*(Note: If no OpenAI API key is provided, FinAssist will fall back to its internal financial rule engine so the AI assistant continues to answer database and calculation questions out-of-the-box!)*

### 6. Start Flask Server
```powershell
python backend\app.py
```

### 7. Open Application in Browser
Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## Verification & Testing Commands

To run automated backend calculation and database unit tests:
```powershell
python backend\test_backend.py
```
