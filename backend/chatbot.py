"""
FinAssist - AI Finance Chatbot Engine
Integrates OpenAI API with local SQLite Database and Financial Calculation Engine.
Enforces accurate data retrieval and zero financial hallucination.
"""

import os
import sys
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
from backend.calculations import calculate_loan_summary
import backend.database as db

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# OpenAI Function / Tool Definitions
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "calculate_loan_proposal",
            "description": "Calculate loan repayment, total interest, monthly/weekly/daily payments for a proposed loan. DO NOT guess calculations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "principal": {"type": "number", "description": "Principal loan amount in INR"},
                    "interest_rate": {"type": "number", "description": "Interest rate percentage (e.g., 2 for 2%)"},
                    "interest_type": {"type": "string", "enum": ["flat", "reducing"], "description": "Type of interest: flat or reducing"},
                    "duration_months": {"type": "integer", "description": "Duration of loan in months"},
                    "payment_frequency": {"type": "string", "enum": ["monthly", "weekly", "daily"], "description": "Frequency of repayment"}
                },
                "required": ["principal", "interest_rate", "duration_months"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_customer_info",
            "description": "Retrieve existing customer details, outstanding balance, active loans, and remaining loan duration from the database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_name_or_id": {"type": "string", "description": "Full name, partial name, or ID of customer"}
                },
                "required": ["customer_name_or_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_todays_collections",
            "description": "Get total payments collected today.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_overdue_list",
            "description": "Get a list of customers and loans with overdue payments.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_dashboard_summary",
            "description": "Get aggregate financial dashboard summary including total lent, total repaid, total outstanding, expected interest.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    }
]

SYSTEM_PROMPT = """You are FinAssist AI, an expert financial assistant for a small finance business.
Your primary rule: NEVER INVENT OR HALLUCINATE FINANCIAL NUMBERS.

- When asked for financial calculations (e.g. "₹50,000 for 12 months at 2% interest"), execute the `calculate_loan_proposal` function.
- When asked about existing customers (e.g. "How much is remaining for Ravi?", "How many months left for Arun?"), execute the `get_customer_info` function.
- When asked about collections or overdue payments, execute the corresponding database query functions (`get_todays_collections`, `get_overdue_list`).
- Present financial numbers clearly formatted in Indian Rupees (₹), showing Principal, Interest Rate, Duration, Total Interest, Total Repayment, and Monthly/Weekly/Daily payments.
- If the user query lacks clarity on whether interest rate is monthly or yearly, or flat vs reducing balance, assume 2% per month flat unless specified, but state your assumption clearly.
"""

def execute_tool_call(tool_name, arguments):
    """Executes backend functions based on AI tool requests."""
    if tool_name == "calculate_loan_proposal":
        principal = float(arguments.get("principal", 0))
        rate = float(arguments.get("interest_rate", 2.0))
        itype = arguments.get("interest_type", "flat")
        duration = int(arguments.get("duration_months", 12))
        freq = arguments.get("payment_frequency", "monthly")
        
        summary = calculate_loan_summary(principal, rate, itype, duration, "2026-09-09", freq)
        return summary

    elif tool_name == "get_customer_info":
        query = arguments.get("customer_name_or_id", "").strip()
        customers = db.get_customers(query)
        if not customers:
            return {"status": "not_found", "message": f"No customer found matching '{query}'"}
        
        # Get full details of best match
        cust_details = db.get_customer_by_id(customers[0]['id'])
        return cust_details

    elif tool_name == "get_todays_collections":
        summary = db.get_dashboard_summary()
        return {"todays_collections": summary['todays_collections']}

    elif tool_name == "get_overdue_list":
        summary = db.get_dashboard_summary()
        return {"overdue_payments": summary['overdue_payments']}

    elif tool_name == "get_dashboard_summary":
        return db.get_dashboard_summary()

    return {"error": f"Unknown function: {tool_name}"}

def process_chat_message(user_message):
    """
    Processes a user chat message using OpenAI Chat Completion API with tool execution,
    or falls back to database & calculation rules if no API key is available.
    """
    # Record user message in DB
    db.add_chat_message("user", user_message)

    api_key = os.getenv("OPENAI_API_KEY") or OPENAI_API_KEY
    if not api_key or api_key == "YOUR_OPENAI_API_KEY_HERE":
        # Rule-based fallback if OpenAI key is not configured
        bot_response = fallback_chat_response(user_message)
        db.add_chat_message("assistant", bot_response)
        return bot_response

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ]

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.2
        )

        response_message = response.choices[0].message

        if response_message.tool_calls:
            messages.append(response_message)
            for tool_call in response_message.tool_calls:
                func_name = tool_call.function.name
                func_args = json.loads(tool_call.function.arguments)
                tool_result = execute_tool_call(func_name, func_args)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(tool_result, default=str)
                })

            second_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.2
            )
            bot_response = second_response.choices[0].message.content
        else:
            bot_response = response_message.content

    except Exception as e:
        # Graceful fallback on API error or network issue
        bot_response = fallback_chat_response(user_message, str(e))

    db.add_chat_message("assistant", bot_response)
    return bot_response

def fallback_chat_response(user_message, error_detail=None):
    """Rule-based engine when OpenAI API key is unavailable or fails."""
    msg = user_message.lower()

    # Search for customer inquiry
    import re
    
    # 1. Calculation request detection (e.g., 50000, 2%, 10 months)
    numbers = re.findall(r'₹?\s*(\d[\d,.]*)', user_message)
    if ("calculate" in msg or "gave" in msg or "interest" in msg) and len(numbers) >= 2:
        try:
            clean_nums = [float(n.replace(',', '')) for n in numbers]
            principal = max(clean_nums)
            duration = 12
            rate = 2.0

            # Find rate and duration if specified
            for num in clean_nums:
                if num != principal:
                    if num <= 50 and rate == 2.0:
                        rate = num
                    elif num > 0:
                        duration = int(num)

            summary = calculate_loan_summary(principal, rate, "flat", duration, "2026-09-09", "monthly")
            return f"""### Loan Calculation Summary (Flat Interest)

- **Principal**: ₹{summary['principal']:,.2f}
- **Interest Rate**: {summary['interest_rate']}% per month
- **Duration**: {summary['duration_months']} months
- **Total Interest**: ₹{summary['total_interest']:,.2f}
- **Total Repayment**: ₹{summary['total_repayment']:,.2f}
- **Monthly Payment**: ₹{summary['monthly_payment']:,.2f}
- **Weekly Payment**: ₹{summary['weekly_payment']:,.2f}
- **Daily Payment**: ₹{summary['daily_payment']:,.2f}

*(Calculated via FinAssist Calculation Engine)*"""
        except Exception:
            pass

    # 2. Today's collections
    if "today" in msg or "collection" in msg:
        summary = db.get_dashboard_summary()
        return f"**Today's Collections**: ₹{summary['todays_collections']:,.2f}"

    # 3. Overdue inquiry
    if "overdue" in msg or "pending" in msg:
        summary = db.get_dashboard_summary()
        overdue = summary['overdue_payments']
        if not overdue:
            return "There are currently **no overdue payments**."
        
        out = "### Overdue Payments:\n\n"
        for item in overdue:
            out += f"- **{item['customer_name']}** (Phone: {item['customer_phone']}): Due ₹{item['total_due']:,.2f} on {item['due_date']}\n"
        return out

    # 4. Customer balance inquiry
    words = user_message.split()
    for word in words:
        clean_word = word.strip("?,.!")
        if len(clean_word) > 2 and clean_word.lower() not in ['how', 'much', 'is', 'for', 'the', 'what', 'who', 'show', 'give']:
            custs = db.get_customers(clean_word)
            if custs:
                c = db.get_customer_by_id(custs[0]['id'])
                out = f"### Customer Profile: {c['full_name']}\n"
                out += f"- **Phone**: {c['phone']}\n"
                out += f"- **Total Loans**: {len(c['loans'])}\n"
                out += f"- **Total Paid**: ₹{c['total_paid']:,.2f}\n"
                out += f"- **Outstanding Balance**: ₹{c['total_outstanding']:,.2f}\n\n"
                if c['loans']:
                    out += "#### Active Loans:\n"
                    for l in c['loans']:
                        out += f"- Loan #{l['id']}: Principal ₹{l['principal']:,.2f}, Outstanding ₹{l['outstanding_balance']:,.2f}, End Date: {l['end_date']} (Status: {l['status']})\n"
                return out

    # General Dashboard Summary
    dash = db.get_dashboard_summary()
    return f"""### FinAssist Summary Overview

- **Total Customers**: {dash['total_customers']}
- **Active Loans**: {dash['active_loans']}
- **Total Amount Lent**: ₹{dash['total_amount_lent']:,.2f}
- **Total Outstanding**: ₹{dash['total_outstanding']:,.2f}
- **Today's Collections**: ₹{dash['todays_collections']:,.2f}

*How can I help you with calculations, customer details, or loans today?*"""
