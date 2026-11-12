"""
FinAssist - Flask Server Application
Exposes REST APIs for Customers, Loans, Repayment Schedules, Payments, Financial Calculations, Reports, and AI Chatbot.
Serves Frontend static HTML/CSS/JS files cleanly.
"""

import os
import sys
import csv
import io

# Ensure root workspace is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, jsonify, request, send_from_directory, Response
from flask_cors import CORS
from dotenv import load_dotenv

# Import backend modules
import backend.database as db
import backend.calculations as calc
import backend.chatbot as bot

load_dotenv()

FRONTEND_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))

app = Flask(__name__, static_folder=FRONTEND_FOLDER, static_url_path='')
CORS(app)

# Initialize SQLite Database
db.init_db()

# ----------------- PAGE ROUTES -----------------

@app.route('/')
def root():
    return send_from_directory(FRONTEND_FOLDER, 'dashboard.html')

@app.route('/<path:filename>')
def serve_static(filename):
    if os.path.exists(os.path.join(FRONTEND_FOLDER, filename)):
        return send_from_directory(FRONTEND_FOLDER, filename)
    elif filename.endswith('.html') or not '.' in filename:
        page = filename if filename.endswith('.html') else f"{filename}.html"
        if os.path.exists(os.path.join(FRONTEND_FOLDER, page)):
            return send_from_directory(FRONTEND_FOLDER, page)
    return send_from_directory(FRONTEND_FOLDER, 'dashboard.html')

# ----------------- DASHBOARD API -----------------

@app.route('/api/dashboard', methods=['GET'])
def get_dashboard():
    try:
        data = db.get_dashboard_summary()
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ----------------- CUSTOMERS API -----------------

@app.route('/api/customers', methods=['GET'])
def list_customers():
    try:
        search_query = request.args.get('q', None)
        customers = db.get_customers(search_query)
        return jsonify({"success": True, "customers": customers})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/customers', methods=['POST'])
def add_customer():
    try:
        body = request.get_json() or {}
        full_name = body.get('full_name')
        phone = body.get('phone')
        address = body.get('address', '')
        notes = body.get('notes', '')

        if not full_name or not phone:
            return jsonify({"success": False, "error": "Customer Full Name and Phone Number are required."}), 400

        customer = db.add_customer(full_name, phone, address, notes)
        return jsonify({"success": True, "customer": customer}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/customers/<int:customer_id>', methods=['GET'])
def get_customer(customer_id):
    try:
        customer = db.get_customer_by_id(customer_id)
        if not customer:
            return jsonify({"success": False, "error": f"Customer #{customer_id} not found."}), 404
        return jsonify({"success": True, "customer": customer})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/customers/<int:customer_id>', methods=['PUT'])
def update_customer(customer_id):
    try:
        body = request.get_json() or {}
        full_name = body.get('full_name')
        phone = body.get('phone')
        address = body.get('address', '')
        notes = body.get('notes', '')

        if not full_name or not phone:
            return jsonify({"success": False, "error": "Full Name and Phone are required."}), 400

        customer = db.update_customer(customer_id, full_name, phone, address, notes)
        return jsonify({"success": True, "customer": customer})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/customers/<int:customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    try:
        db.delete_customer(customer_id)
        return jsonify({"success": True, "message": f"Customer #{customer_id} deleted successfully."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ----------------- LOANS API -----------------

@app.route('/api/loans', methods=['GET'])
def list_loans():
    try:
        status_filter = request.args.get('status', None)
        customer_id = request.args.get('customer_id', None)
        loans = db.get_loans(status_filter=status_filter, customer_id=customer_id)
        return jsonify({"success": True, "loans": loans})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/loans', methods=['POST'])
def create_loan():
    try:
        body = request.get_json() or {}
        customer_id = body.get('customer_id')
        principal = body.get('principal')
        interest_rate = body.get('interest_rate')
        interest_type = body.get('interest_type', 'flat')
        duration_months = body.get('duration_months')
        start_date = body.get('start_date')
        payment_frequency = body.get('payment_frequency', 'monthly')

        if not all([customer_id, principal, interest_rate, duration_months, start_date]):
            return jsonify({"success": False, "error": "Missing required loan fields: customer_id, principal, interest_rate, duration_months, start_date."}), 400

        if float(principal) <= 0:
            return jsonify({"success": False, "error": "Principal must be greater than zero."}), 400
        if float(interest_rate) < 0:
            return jsonify({"success": False, "error": "Interest rate cannot be negative."}), 400
        if int(duration_months) <= 0:
            return jsonify({"success": False, "error": "Duration must be greater than 0 months."}), 400

        loan = db.create_loan(
            customer_id=int(customer_id),
            principal=float(principal),
            interest_rate=float(interest_rate),
            interest_type=interest_type,
            duration_months=int(duration_months),
            start_date_str=start_date,
            payment_frequency=payment_frequency
        )
        return jsonify({"success": True, "loan": loan}), 201
    except ValueError as ve:
        return jsonify({"success": False, "error": str(ve)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/loans/<int:loan_id>', methods=['GET'])
def get_loan(loan_id):
    try:
        loan = db.get_loan_by_id(loan_id)
        if not loan:
            return jsonify({"success": False, "error": f"Loan #{loan_id} not found."}), 404
        return jsonify({"success": True, "loan": loan})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/loans/<int:loan_id>', methods=['DELETE'])
def delete_loan(loan_id):
    try:
        db.delete_loan(loan_id)
        return jsonify({"success": True, "message": f"Loan #{loan_id} deleted."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ----------------- PAYMENTS API -----------------

@app.route('/api/payments', methods=['GET'])
def list_payments():
    try:
        payments = db.get_payments()
        return jsonify({"success": True, "payments": payments})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/payments', methods=['POST'])
def record_payment():
    try:
        body = request.get_json() or {}
        loan_id = body.get('loan_id')
        amount_paid = body.get('amount_paid')
        payment_method = body.get('payment_method', 'Cash')
        payment_date = body.get('payment_date')
        notes = body.get('notes', '')

        if not loan_id or not amount_paid:
            return jsonify({"success": False, "error": "loan_id and amount_paid are required."}), 400

        if float(amount_paid) <= 0:
            return jsonify({"success": False, "error": "Payment amount must be greater than zero."}), 400

        updated_loan = db.record_payment(
            loan_id=int(loan_id),
            amount_paid=float(amount_paid),
            payment_method=payment_method,
            payment_date=payment_date,
            notes=notes
        )
        return jsonify({"success": True, "loan": updated_loan}), 201
    except ValueError as ve:
        return jsonify({"success": False, "error": str(ve)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ----------------- CALCULATOR API -----------------

@app.route('/api/calculate-loan', methods=['POST'])
def calculate_loan_api():
    try:
        body = request.get_json() or {}
        principal = float(body.get('principal', 0))
        interest_rate = float(body.get('interest_rate', 0))
        interest_type = body.get('interest_type', 'flat')
        duration_months = int(body.get('duration_months', 1))
        start_date = body.get('start_date', '2026-09-09')
        payment_frequency = body.get('payment_frequency', 'monthly')

        if principal <= 0 or duration_months <= 0:
            return jsonify({"success": False, "error": "Principal and duration must be greater than zero."}), 400

        result = calc.calculate_loan_summary(
            principal=principal,
            interest_rate=interest_rate,
            interest_type=interest_type,
            duration_months=duration_months,
            start_date_str=start_date,
            payment_frequency=payment_frequency
        )
        return jsonify({"success": True, "calculation": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ----------------- CHATBOT API -----------------

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        body = request.get_json() or {}
        message = body.get('message', '').strip()

        if not message:
            return jsonify({"success": False, "error": "Message content cannot be empty."}), 400

        bot_reply = bot.process_chat_message(message)
        return jsonify({"success": True, "response": bot_reply})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/chat/history', methods=['GET'])
def chat_history():
    try:
        history = db.get_chat_history()
        return jsonify({"success": True, "history": history})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/chat/history', methods=['DELETE'])
def clear_history():
    try:
        db.clear_chat_history()
        return jsonify({"success": True, "message": "Chat history cleared."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ----------------- REPORTS & SEARCH API -----------------

@app.route('/api/reports', methods=['GET'])
def get_reports():
    try:
        reports = db.get_reports_summary()
        return jsonify({"success": True, "reports": reports})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/reports/export', methods=['GET'])
def export_reports_csv():
    try:
        payments = db.get_payments()
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write CSV Header
        writer.writerow(['Payment ID', 'Loan ID', 'Customer Name', 'Payment Date', 'Amount Paid (₹)', 'Payment Method', 'Notes'])
        
        for p in payments:
            writer.writerow([
                p['id'], p['loan_id'], p['customer_name'], p['payment_date'],
                f"{p['amount_paid']:.2f}", p['payment_method'], p.get('notes', '')
            ])
            
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment;filename=finassist_payments_report.csv"}
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/search', methods=['GET'])
def search_all():
    try:
        q = request.args.get('q', '')
        results = db.global_search(q)
        return jsonify({"success": True, "results": results})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ----------------- SERVER ENTRY -----------------

if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 5000))
    print(f"FinAssist Backend Server running on http://127.0.0.1:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)
