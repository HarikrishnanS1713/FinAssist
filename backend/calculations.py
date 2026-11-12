"""
FinAssist - Financial Calculation Engine
Handles interest calculations (Flat and Reducing Balance), repayment breakdown, and schedule generation.
"""

from datetime import datetime, timedelta
import calendar

def add_months(sourcedate, months):
    """Utility to add months to a datetime object accurately."""
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month // 12
    month = month % 12 + 1
    day = min(sourcedate.day, calendar.monthrange(year, month)[1])
    return datetime(year, month, day)

def calculate_loan_summary(principal: float, interest_rate: float, interest_type: str, duration_months: int, start_date_str: str, payment_frequency: str = 'monthly'):
    """
    Calculates principal, total interest, total repayment, periodic payment amounts, number of payments, and generates schedule.
    
    :param principal: Principal amount in INR
    :param interest_rate: Interest rate percentage per month (e.g., 2 for 2%)
    :param interest_type: 'flat' or 'reducing'
    :param duration_months: Loan duration in months
    :param start_date_str: Start date ISO format 'YYYY-MM-DD'
    :param payment_frequency: 'daily', 'weekly', or 'monthly'
    :return: dict with detailed breakdown and repayment schedule
    """
    if principal <= 0:
        raise ValueError("Principal amount must be greater than zero.")
    if interest_rate < 0:
        raise ValueError("Interest rate cannot be negative.")
    if duration_months <= 0:
        raise ValueError("Duration in months must be greater than zero.")

    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    except Exception:
        start_date = datetime.now()

    interest_type = interest_type.lower().strip()
    payment_frequency = payment_frequency.lower().strip()

    # Determine end date and number of payments based on frequency
    if payment_frequency == 'daily':
        end_date = start_date + timedelta(days=duration_months * 30)
        num_payments = duration_months * 30
    elif payment_frequency == 'weekly':
        end_date = start_date + timedelta(weeks=duration_months * 4)
        num_payments = duration_months * 4
    else:  # monthly
        end_date = add_months(start_date, duration_months)
        num_payments = duration_months

    rate_per_month = interest_rate / 100.0

    if interest_type == 'flat':
        total_interest = round(principal * rate_per_month * duration_months, 2)
        total_repayment = round(principal + total_interest, 2)
        periodic_payment = round(total_repayment / num_payments, 2)
        
        # Monthly, weekly, daily estimations for UI display
        monthly_payment = round(total_repayment / duration_months, 2)
        weekly_payment = round(total_repayment / (duration_months * 4), 2)
        daily_payment = round(total_repayment / (duration_months * 30), 2)
    
    elif interest_type == 'reducing':
        # Reducing balance (EMI) calculation
        if rate_per_month > 0:
            emi = principal * rate_per_month * ((1 + rate_per_month) ** duration_months) / (((1 + rate_per_month) ** duration_months) - 1)
        else:
            emi = principal / duration_months
        
        monthly_payment = round(emi, 2)
        total_repayment = round(monthly_payment * duration_months, 2)
        total_interest = round(total_repayment - principal, 2)

        if payment_frequency == 'monthly':
            periodic_payment = monthly_payment
        elif payment_frequency == 'weekly':
            num_payments = duration_months * 4
            periodic_payment = round(total_repayment / num_payments, 2)
        else: # daily
            num_payments = duration_months * 30
            periodic_payment = round(total_repayment / num_payments, 2)

        weekly_payment = round(total_repayment / (duration_months * 4), 2)
        daily_payment = round(total_repayment / (duration_months * 30), 2)
    else:
        raise ValueError("Invalid interest type. Choose 'flat' or 'reducing'.")

    # Generate Repayment Schedule
    schedule = []
    rem_balance = total_repayment
    curr_principal_rem = principal
    curr_date = start_date

    for i in range(1, num_payments + 1):
        if payment_frequency == 'daily':
            curr_date = curr_date + timedelta(days=1)
        elif payment_frequency == 'weekly':
            curr_date = curr_date + timedelta(weeks=1)
        else:  # monthly
            curr_date = add_months(start_date, i)

        due_date_str = curr_date.strftime('%Y-%m-%d')

        if interest_type == 'flat':
            p_comp = round(principal / num_payments, 2)
            i_comp = round(total_interest / num_payments, 2)
        else:  # reducing
            if payment_frequency == 'monthly':
                i_comp = round(curr_principal_rem * rate_per_month, 2)
                p_comp = round(periodic_payment - i_comp, 2)
                if i == num_payments or p_comp > curr_principal_rem:
                    p_comp = round(curr_principal_rem, 2)
                curr_principal_rem = max(0.0, round(curr_principal_rem - p_comp, 2))
            else:
                p_comp = round(principal / num_payments, 2)
                i_comp = round(total_interest / num_payments, 2)

        tot_due = round(p_comp + i_comp, 2)
        
        # Last payment adjustment for total repayment match
        if i == num_payments:
            tot_due = round(rem_balance, 2)

        rem_balance = max(0.0, round(rem_balance - tot_due, 2))

        schedule.append({
            "payment_number": i,
            "due_date": due_date_str,
            "principal_component": p_comp,
            "interest_component": i_comp,
            "total_due": tot_due,
            "amount_paid": 0.0,
            "remaining_balance": rem_balance,
            "status": "Pending"
        })

    return {
        "principal": round(principal, 2),
        "interest_rate": interest_rate,
        "interest_type": interest_type,
        "duration_months": duration_months,
        "start_date": start_date_str,
        "end_date": end_date.strftime('%Y-%m-%d'),
        "payment_frequency": payment_frequency,
        "total_interest": total_interest,
        "total_repayment": total_repayment,
        "monthly_payment": monthly_payment,
        "weekly_payment": weekly_payment,
        "daily_payment": daily_payment,
        "num_payments": num_payments,
        "periodic_payment": periodic_payment,
        "schedule": schedule
    }
