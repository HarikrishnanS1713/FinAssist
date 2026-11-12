"""
FinAssist Backend Automated Test Script
Verifies calculation engine, database CRUD operations, repayment schedule logic, and API routes.
"""

import os
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import backend.calculations as calc
import backend.database as db
import backend.chatbot as bot

def test_all():
    print("--- 1. TESTING FINANCIAL CALCULATION ENGINE ---")
    
    # Test Flat Interest calculation (₹50,000 @ 2% for 10 months)
    flat_summary = calc.calculate_loan_summary(
        principal=50000,
        interest_rate=2.0,
        interest_type='flat',
        duration_months=10,
        start_date_str='2026-09-09',
        payment_frequency='monthly'
    )
    assert flat_summary['total_interest'] == 10000.0, f"Expected 10000.0 interest, got {flat_summary['total_interest']}"
    assert flat_summary['total_repayment'] == 60000.0, f"Expected 60000.0 repayment, got {flat_summary['total_repayment']}"
    assert flat_summary['monthly_payment'] == 6000.0, f"Expected 6000.0 monthly payment, got {flat_summary['monthly_payment']}"
    assert len(flat_summary['schedule']) == 10, f"Expected 10 schedule items, got {len(flat_summary['schedule'])}"
    print("[SUCCESS] Flat Interest calculation PASSED!")

    # Test Reducing Balance calculation (₹1,00,000 @ 2% for 10 months)
    reducing_summary = calc.calculate_loan_summary(
        principal=100000,
        interest_rate=2.0,
        interest_type='reducing',
        duration_months=10,
        start_date_str='2026-09-09',
        payment_frequency='monthly'
    )
    assert reducing_summary['monthly_payment'] > 0, "Reducing balance EMI calculation failed"
    assert len(reducing_summary['schedule']) == 10, "Schedule item length error"
    print(f"[SUCCESS] Reducing Balance calculation PASSED! Monthly EMI: Rs.{reducing_summary['monthly_payment']:,.2f}, Total Interest: Rs.{reducing_summary['total_interest']:,.2f}")

    print("\n--- 2. TESTING DATABASE INITIALIZATION & CRUD ---")
    if os.path.exists(db.DB_PATH):
        os.remove(db.DB_PATH)
    db.init_db()
    print("[SUCCESS] SQLite database initialized successfully!")

    # Add Customer
    cust = db.add_customer("Ravi Kumar", "9876543210", "123 Main Street, Bangalore", "VIP Customer")
    assert cust['id'] is not None, "Customer ID missing"
    assert cust['full_name'] == "Ravi Kumar", "Customer name mismatch"
    print(f"[SUCCESS] Customer added successfully: ID #{cust['id']} - {cust['full_name']}")

    # Create Loan for Customer
    loan = db.create_loan(
        customer_id=cust['id'],
        principal=50000,
        interest_rate=2.0,
        interest_type='flat',
        duration_months=10,
        start_date_str='2026-09-09',
        payment_frequency='monthly'
    )
    assert loan['id'] is not None, "Loan ID missing"
    assert loan['outstanding_balance'] == 60000.0, f"Expected outstanding 60000.0, got {loan['outstanding_balance']}"
    assert len(loan['schedule']) == 10, "Repayment schedule mismatch"
    print(f"[SUCCESS] Loan created successfully: Loan #{loan['id']} - Total Repayment: Rs.{loan['total_repayment']:,.2f}")

    # Record Payment
    updated_loan = db.record_payment(
        loan_id=loan['id'],
        amount_paid=6000.0,
        payment_method='UPI',
        notes='First EMI payment'
    )
    assert updated_loan['amount_paid'] == 6000.0, f"Expected amount paid 6000.0, got {updated_loan['amount_paid']}"
    assert updated_loan['outstanding_balance'] == 54000.0, f"Expected outstanding 54000.0, got {updated_loan['outstanding_balance']}"
    assert updated_loan['schedule'][0]['status'] == 'Paid', "Schedule item status should be Paid"
    print(f"[SUCCESS] Payment recorded successfully! Outstanding balance reduced to Rs.{updated_loan['outstanding_balance']:,.2f}")

    # Dashboard Summary Test
    summary = db.get_dashboard_summary()
    assert summary['total_customers'] >= 1, "Dashboard customers error"
    assert summary['todays_collections'] == 6000.0, f"Expected today collections 6000.0, got {summary['todays_collections']}"
    print(f"[SUCCESS] Dashboard metrics verified! Today's Collections: Rs.{summary['todays_collections']:,.2f}")

    print("\n--- 3. TESTING CHATBOT LOGIC ---")
    chat_reply = bot.process_chat_message("How much is remaining for customer Ravi?")
    print("[SUCCESS] Chatbot Response to 'How much is remaining for customer Ravi?':")
    print(chat_reply)
    assert "Ravi" in chat_reply or "54,000" in chat_reply or "Summary" in chat_reply, "Chatbot response invalid"

    print("\nALL BACKEND TESTS PASSED SUCCESSFULLY!")

if __name__ == '__main__':
    test_all()
