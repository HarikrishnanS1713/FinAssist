"""
FinAssist Live HTTP REST API Integration Test Script
Tests all Flask REST API endpoints over HTTP on http://127.0.0.1:5000.
"""

import sys
import io
import urllib.request
import json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_URL = "http://127.0.0.1:5000"

def get(path):
    req = urllib.request.Request(f"{BASE_URL}{path}")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode('utf-8'))

def post(path, body):
    data = json.dumps(body).encode('utf-8')
    req = urllib.request.Request(f"{BASE_URL}{path}", data=data, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode('utf-8'))

def run_integration_tests():
    print("--- TESTING LIVE FLASK REST APIS ---")

    # 1. Dashboard
    dash = get('/api/dashboard')
    assert dash['success'] == True
    print("[SUCCESS] GET /api/dashboard OK!")

    # 2. Add Customer "Arun Verma"
    cust_resp = post('/api/customers', {
        "full_name": "Arun Verma",
        "phone": "9123456789",
        "address": "456 Park Road, Delhi",
        "notes": "Business owner"
    })
    assert cust_resp['success'] == True
    arun_id = cust_resp['customer']['id']
    print(f"[SUCCESS] POST /api/customers OK! Customer ID #{arun_id} created.")

    # 3. Issue Loan for Arun Verma (₹1,00,000 @ 2% for 10 months)
    loan_resp = post('/api/loans', {
        "customer_id": arun_id,
        "principal": 100000,
        "interest_rate": 2.0,
        "interest_type": "flat",
        "duration_months": 10,
        "start_date": "2026-09-09",
        "payment_frequency": "monthly"
    })
    assert loan_resp['success'] == True
    loan_id = loan_resp['loan']['id']
    print(f"[SUCCESS] POST /api/loans OK! Loan #{loan_id} created. Repayment: Rs.{loan_resp['loan']['total_repayment']}")

    # 4. Standalone Calculator API
    calc_resp = post('/api/calculate-loan', {
        "principal": 50000,
        "interest_rate": 2.0,
        "interest_type": "reducing",
        "duration_months": 12,
        "start_date": "2026-09-09",
        "payment_frequency": "monthly"
    })
    assert calc_resp['success'] == True
    print(f"[SUCCESS] POST /api/calculate-loan OK! EMI: Rs.{calc_resp['calculation']['monthly_payment']}")

    # 5. Record Payment for Arun Verma
    pay_resp = post('/api/payments', {
        "loan_id": loan_id,
        "amount_paid": 12000,
        "payment_method": "Bank Transfer",
        "payment_date": "2026-09-09",
        "notes": "First installment payment"
    })
    assert pay_resp['success'] == True
    print(f"[SUCCESS] POST /api/payments OK! Updated outstanding balance: Rs.{pay_resp['loan']['outstanding_balance']}")

    # 6. AI Chatbot API
    chat_resp = post('/api/chat', {
        "message": "How much is remaining for customer Arun?"
    })
    assert chat_resp['success'] == True
    print("[SUCCESS] POST /api/chat OK! Chatbot Reply:")
    print(chat_resp['response'])

    # 7. Reports API
    rep_resp = get('/api/reports')
    assert rep_resp['success'] == True
    print("[SUCCESS] GET /api/reports OK!")

    print("\nALL FLASK REST API INTEGRATION TESTS PASSED PERFECTLY!")

if __name__ == '__main__':
    run_integration_tests()
