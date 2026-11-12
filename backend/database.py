"""
FinAssist - SQLite Database Module
Manages database connection, tables initialization, and all CRUD operations for customers, loans, repayment schedules, payments, and chat messages.
"""

import sqlite3
import os
import sys
from datetime import datetime, date

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.calculations import calculate_loan_summary

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'finance.db')

def get_db_connection():
    """Establishes and returns a SQLite database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    """Initializes SQLite database tables."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Customers Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        phone TEXT NOT NULL,
        address TEXT,
        date_added TEXT NOT NULL,
        notes TEXT
    );
    """)

    # Loans Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS loans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        principal REAL NOT NULL,
        interest_rate REAL NOT NULL,
        interest_type TEXT NOT NULL,
        duration_months INTEGER NOT NULL,
        start_date TEXT NOT NULL,
        end_date TEXT NOT NULL,
        payment_frequency TEXT NOT NULL,
        total_interest REAL NOT NULL,
        total_repayment REAL NOT NULL,
        amount_paid REAL DEFAULT 0.0,
        outstanding_balance REAL NOT NULL,
        status TEXT NOT NULL DEFAULT 'Active',
        created_at TEXT NOT NULL,
        FOREIGN KEY (customer_id) REFERENCES customers (id) ON DELETE CASCADE
    );
    """)

    # Repayment Schedule Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS repayment_schedule (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        loan_id INTEGER NOT NULL,
        payment_number INTEGER NOT NULL,
        due_date TEXT NOT NULL,
        principal_component REAL NOT NULL,
        interest_component REAL NOT NULL,
        total_due REAL NOT NULL,
        amount_paid REAL DEFAULT 0.0,
        remaining_balance REAL NOT NULL,
        status TEXT NOT NULL DEFAULT 'Pending',
        FOREIGN KEY (loan_id) REFERENCES loans (id) ON DELETE CASCADE
    );
    """)

    # Payments Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        loan_id INTEGER NOT NULL,
        customer_id INTEGER NOT NULL,
        payment_date TEXT NOT NULL,
        amount_paid REAL NOT NULL,
        payment_method TEXT NOT NULL,
        notes TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (loan_id) REFERENCES loans (id) ON DELETE CASCADE,
        FOREIGN KEY (customer_id) REFERENCES customers (id) ON DELETE CASCADE
    );
    """)

    # Chat Messages Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT NOT NULL,
        message TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    """)

    conn.commit()
    conn.close()

# ----------------- CUSTOMER FUNCTIONS -----------------

def add_customer(full_name, phone, address="", notes=""):
    conn = get_db_connection()
    cursor = conn.cursor()
    date_added = date.today().isoformat()
    cursor.execute("""
        INSERT INTO customers (full_name, phone, address, date_added, notes)
        VALUES (?, ?, ?, ?, ?)
    """, (full_name.strip(), phone.strip(), address.strip(), date_added, notes.strip()))
    customer_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return get_customer_by_id(customer_id)

def get_customers(search_query=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    if search_query:
        query = f"%{search_query.strip()}%"
        cursor.execute("""
            SELECT c.*, 
                   COUNT(l.id) as total_loans,
                   COALESCE(SUM(l.outstanding_balance), 0) as current_outstanding
            FROM customers c
            LEFT JOIN loans l ON c.id = l.customer_id
            WHERE c.full_name LIKE ? OR c.phone LIKE ? OR CAST(c.id AS TEXT) LIKE ?
            GROUP BY c.id
            ORDER BY c.id DESC
        """, (query, query, query))
    else:
        cursor.execute("""
            SELECT c.*, 
                   COUNT(l.id) as total_loans,
                   COALESCE(SUM(l.outstanding_balance), 0) as current_outstanding
            FROM customers c
            LEFT JOIN loans l ON c.id = l.customer_id
            GROUP BY c.id
            ORDER BY c.id DESC
        """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_customer_by_id(customer_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    customer = dict(row)
    
    # Get loans for customer
    cursor.execute("SELECT * FROM loans WHERE customer_id = ? ORDER BY id DESC", (customer_id,))
    loans = [dict(r) for r in cursor.fetchall()]
    
    # Get total outstanding & total paid
    cursor.execute("""
        SELECT COALESCE(SUM(outstanding_balance), 0) as total_outstanding,
               COALESCE(SUM(amount_paid), 0) as total_paid
        FROM loans WHERE customer_id = ?
    """, (customer_id,))
    totals = cursor.fetchone()
    
    customer['loans'] = loans
    customer['total_outstanding'] = totals['total_outstanding'] if totals else 0.0
    customer['total_paid'] = totals['total_paid'] if totals else 0.0
    
    conn.close()
    return customer

def update_customer(customer_id, full_name, phone, address="", notes=""):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE customers 
        SET full_name = ?, phone = ?, address = ?, notes = ?
        WHERE id = ?
    """, (full_name.strip(), phone.strip(), address.strip(), notes.strip(), customer_id))
    conn.commit()
    conn.close()
    return get_customer_by_id(customer_id)

def delete_customer(customer_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
    conn.commit()
    conn.close()
    return True

# ----------------- LOAN FUNCTIONS -----------------

def create_loan(customer_id, principal, interest_rate, interest_type, duration_months, start_date_str, payment_frequency='monthly'):
    customer = get_customer_by_id(customer_id)
    if not customer:
        raise ValueError(f"Customer with ID {customer_id} does not exist.")
    
    summary = calculate_loan_summary(
        principal=float(principal),
        interest_rate=float(interest_rate),
        interest_type=interest_type,
        duration_months=int(duration_months),
        start_date_str=start_date_str,
        payment_frequency=payment_frequency
    )

    created_at = datetime.now().isoformat()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO loans (
            customer_id, principal, interest_rate, interest_type, duration_months,
            start_date, end_date, payment_frequency, total_interest, total_repayment,
            amount_paid, outstanding_balance, status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Active', ?)
    """, (
        customer_id, summary['principal'], summary['interest_rate'], summary['interest_type'],
        summary['duration_months'], summary['start_date'], summary['end_date'], summary['payment_frequency'],
        summary['total_interest'], summary['total_repayment'], 0.0, summary['total_repayment'], created_at
    ))

    loan_id = cursor.lastrowid

    # Insert schedule entries
    for item in summary['schedule']:
        cursor.execute("""
            INSERT INTO repayment_schedule (
                loan_id, payment_number, due_date, principal_component, interest_component,
                total_due, amount_paid, remaining_balance, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            loan_id, item['payment_number'], item['due_date'], item['principal_component'],
            item['interest_component'], item['total_due'], 0.0, item['remaining_balance'], 'Pending'
        ))

    conn.commit()
    conn.close()
    return get_loan_by_id(loan_id)

def get_loans(status_filter=None, customer_id=None):
    update_overdue_statuses()
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT l.*, c.full_name as customer_name, c.phone as customer_phone
        FROM loans l
        JOIN customers c ON l.customer_id = c.id
    """
    params = []
    conditions = []

    if status_filter:
        conditions.append("l.status = ?")
        params.append(status_filter)
    if customer_id:
        conditions.append("l.customer_id = ?")
        params.append(customer_id)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY l.id DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_loan_by_id(loan_id):
    update_overdue_statuses()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT l.*, c.full_name as customer_name, c.phone as customer_phone, c.address as customer_address
        FROM loans l
        JOIN customers c ON l.customer_id = c.id
        WHERE l.id = ?
    """, (loan_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None

    loan = dict(row)

    # Get repayment schedule
    cursor.execute("""
        SELECT * FROM repayment_schedule WHERE loan_id = ? ORDER BY payment_number ASC
    """, (loan_id,))
    loan['schedule'] = [dict(r) for r in cursor.fetchall()]

    # Get payment history
    cursor.execute("""
        SELECT * FROM payments WHERE loan_id = ? ORDER BY id DESC
    """, (loan_id,))
    loan['payments'] = [dict(r) for r in cursor.fetchall()]

    conn.close()
    return loan

def delete_loan(loan_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM loans WHERE id = ?", (loan_id,))
    conn.commit()
    conn.close()
    return True

# ----------------- PAYMENT FUNCTIONS -----------------

def record_payment(loan_id, amount_paid, payment_method='Cash', payment_date=None, notes=""):
    amount_paid = float(amount_paid)
    if amount_paid <= 0:
        raise ValueError("Payment amount must be greater than zero.")

    loan = get_loan_by_id(loan_id)
    if not loan:
        raise ValueError(f"Loan with ID {loan_id} not found.")

    if not payment_date:
        payment_date = date.today().isoformat()

    conn = get_db_connection()
    cursor = conn.cursor()

    # Record payment transaction
    cursor.execute("""
        INSERT INTO payments (loan_id, customer_id, payment_date, amount_paid, payment_method, notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (loan_id, loan['customer_id'], payment_date, amount_paid, payment_method, notes, datetime.now().isoformat()))

    # Apply payment to repayment schedule items sequentially
    cursor.execute("""
        SELECT * FROM repayment_schedule WHERE loan_id = ? AND status != 'Paid' ORDER BY payment_number ASC
    """, (loan_id,))
    pending_items = [dict(r) for r in cursor.fetchall()]

    rem_payment = amount_paid
    for item in pending_items:
        if rem_payment <= 0:
            break
        item_due = item['total_due'] - item['amount_paid']
        if rem_payment >= item_due:
            # Fully pay this schedule item
            new_item_paid = item['total_due']
            new_status = 'Paid'
            rem_payment -= item_due
        else:
            # Partially pay
            new_item_paid = item['amount_paid'] + rem_payment
            new_status = 'Partially Paid'
            rem_payment = 0.0

        cursor.execute("""
            UPDATE repayment_schedule
            SET amount_paid = ?, status = ?
            WHERE id = ?
        """, (new_item_paid, new_status, item['id']))

    # Update Loan totals
    new_total_paid = round(loan['amount_paid'] + amount_paid, 2)
    new_outstanding = round(max(0.0, loan['total_repayment'] - new_total_paid), 2)
    new_loan_status = 'Completed' if new_outstanding <= 0 else loan['status']

    cursor.execute("""
        UPDATE loans
        SET amount_paid = ?, outstanding_balance = ?, status = ?
        WHERE id = ?
    """, (new_total_paid, new_outstanding, new_loan_status, loan_id))

    conn.commit()
    conn.close()

    update_overdue_statuses()
    return get_loan_by_id(loan_id)

def get_payments():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.*, c.full_name as customer_name, l.id as loan_id
        FROM payments p
        JOIN customers c ON p.customer_id = c.id
        JOIN loans l ON p.loan_id = l.id
        ORDER BY p.id DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# ----------------- DASHBOARD & STATUS HELPERS -----------------

def update_overdue_statuses():
    """Checks and updates overdue items and loan statuses based on due date."""
    conn = get_db_connection()
    cursor = conn.cursor()
    today_str = date.today().isoformat()

    # Mark schedule entries overdue if past due date and not paid
    cursor.execute("""
        UPDATE repayment_schedule
        SET status = 'Overdue'
        WHERE due_date < ? AND status IN ('Pending', 'Partially Paid')
    """, (today_str,))

    # Update loan status to Overdue if it has overdue schedule entries and is Active
    cursor.execute("""
        UPDATE loans
        SET status = 'Overdue'
        WHERE id IN (
            SELECT DISTINCT loan_id FROM repayment_schedule WHERE status = 'Overdue'
        ) AND status = 'Active'
    """)

    conn.commit()
    conn.close()

def get_dashboard_summary():
    update_overdue_statuses()
    conn = get_db_connection()
    cursor = conn.cursor()

    today_str = date.today().isoformat()

    cursor.execute("SELECT COUNT(*) as total FROM customers")
    total_customers = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) as total FROM loans WHERE status != 'Completed'")
    active_loans = cursor.fetchone()['total']

    cursor.execute("SELECT COALESCE(SUM(principal), 0) as total FROM loans")
    total_amount_lent = cursor.fetchone()['total']

    cursor.execute("SELECT COALESCE(SUM(amount_paid), 0) as total FROM loans")
    total_amount_repaid = cursor.fetchone()['total']

    cursor.execute("SELECT COALESCE(SUM(outstanding_balance), 0) as total FROM loans WHERE status != 'Completed'")
    total_outstanding = cursor.fetchone()['total']

    cursor.execute("SELECT COALESCE(SUM(total_interest), 0) as total FROM loans")
    total_interest_expected = cursor.fetchone()['total']

    cursor.execute("SELECT COALESCE(SUM(amount_paid), 0) as total FROM payments WHERE payment_date = ?", (today_str,))
    todays_collections = cursor.fetchone()['total']

    # Recent customers
    cursor.execute("SELECT * FROM customers ORDER BY id DESC LIMIT 5")
    recent_customers = [dict(r) for r in cursor.fetchall()]

    # Recent loans
    cursor.execute("""
        SELECT l.*, c.full_name as customer_name
        FROM loans l
        JOIN customers c ON l.customer_id = c.id
        ORDER BY l.id DESC LIMIT 5
    """)
    recent_loans = [dict(r) for r in cursor.fetchall()]

    # Upcoming payments (due within 7 days and status pending/partially paid)
    cursor.execute("""
        SELECT s.*, l.customer_id, c.full_name as customer_name, c.phone as customer_phone
        FROM repayment_schedule s
        JOIN loans l ON s.loan_id = l.id
        JOIN customers c ON l.customer_id = c.id
        WHERE s.due_date >= ? AND s.status IN ('Pending', 'Partially Paid')
        ORDER BY s.due_date ASC LIMIT 5
    """, (today_str,))
    upcoming_payments = [dict(r) for r in cursor.fetchall()]

    # Overdue payments
    cursor.execute("""
        SELECT s.*, l.customer_id, c.full_name as customer_name, c.phone as customer_phone
        FROM repayment_schedule s
        JOIN loans l ON s.loan_id = l.id
        JOIN customers c ON l.customer_id = c.id
        WHERE s.status = 'Overdue'
        ORDER BY s.due_date ASC LIMIT 5
    """)
    overdue_payments = [dict(r) for r in cursor.fetchall()]

    conn.close()

    return {
        "total_customers": total_customers,
        "active_loans": active_loans,
        "total_amount_lent": total_amount_lent,
        "total_amount_repaid": total_amount_repaid,
        "total_outstanding": total_outstanding,
        "total_interest_expected": total_interest_expected,
        "todays_collections": todays_collections,
        "recent_customers": recent_customers,
        "recent_loans": recent_loans,
        "upcoming_payments": upcoming_payments,
        "overdue_payments": overdue_payments
    }

def get_reports_summary():
    update_overdue_statuses()
    conn = get_db_connection()
    cursor = conn.cursor()

    # Loan counts by status
    cursor.execute("SELECT status, COUNT(*) as count, SUM(outstanding_balance) as outstanding FROM loans GROUP BY status")
    status_summary = [dict(r) for r in cursor.fetchall()]

    # Daily collections last 30 days
    cursor.execute("""
        SELECT payment_date, SUM(amount_paid) as daily_total
        FROM payments
        GROUP BY payment_date
        ORDER BY payment_date DESC LIMIT 30
    """)
    daily_collections = [dict(r) for r in cursor.fetchall()]

    # Monthly collections
    cursor.execute("""
        SELECT strftime('%Y-%m', payment_date) as month, SUM(amount_paid) as monthly_total
        FROM payments
        GROUP BY month
        ORDER BY month DESC LIMIT 12
    """)
    monthly_collections = [dict(r) for r in cursor.fetchall()]

    # Total interest collected estimation
    cursor.execute("SELECT COALESCE(SUM(amount_paid), 0) as total_collected FROM payments")
    total_paid = cursor.fetchone()['total_collected']

    conn.close()
    return {
        "status_summary": status_summary,
        "daily_collections": daily_collections,
        "monthly_collections": monthly_collections,
        "total_collections": total_paid
    }

def global_search(query_str):
    if not query_str:
        return {"customers": [], "loans": []}
    q = f"%{query_str.strip()}%"
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM customers
        WHERE full_name LIKE ? OR phone LIKE ? OR CAST(id AS TEXT) LIKE ?
        LIMIT 10
    """, (q, q, q))
    customers = [dict(r) for r in cursor.fetchall()]

    cursor.execute("""
        SELECT l.*, c.full_name as customer_name
        FROM loans l
        JOIN customers c ON l.customer_id = c.id
        WHERE CAST(l.id AS TEXT) LIKE ? OR c.full_name LIKE ? OR c.phone LIKE ?
        LIMIT 10
    """, (q, q, q))
    loans = [dict(r) for r in cursor.fetchall()]

    conn.close()
    return {"customers": customers, "loans": loans}

# ----------------- CHAT HISTORY -----------------

def add_chat_message(sender, message):
    conn = get_db_connection()
    cursor = conn.cursor()
    created_at = datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO chat_messages (sender, message, created_at)
        VALUES (?, ?, ?)
    """, (sender, message, created_at))
    conn.commit()
    conn.close()

def get_chat_history(limit=50):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM (
            SELECT * FROM chat_messages ORDER BY id DESC LIMIT ?
        ) ORDER BY id ASC
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def clear_chat_history():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chat_messages")
    conn.commit()
    conn.close()
    return True
