/**
 * FinAssist - Payment Management Controller
 * Handles loading payments log, opening record payment modal, updating loan dropdown options, auto-filling due amounts, and posting transactions.
 */

document.addEventListener('DOMContentLoaded', () => {
  loadPayments();

  // Set today as default payment date
  const dateInput = document.getElementById('payment-date');
  if (dateInput) {
    dateInput.value = new Date().toISOString().split('T')[0];
  }

  // Modal handlers
  const recordBtn = document.getElementById('btn-record-payment');
  const modal = document.getElementById('modal-payment');
  const closeBtn = document.getElementById('btn-close-payment-modal');
  const cancelBtn = document.getElementById('btn-cancel-payment-modal');
  const form = document.getElementById('form-payment');
  const loanSelect = document.getElementById('payment-loan-id');

  if (recordBtn && modal) {
    recordBtn.addEventListener('click', () => openPaymentModal());
  }

  if (closeBtn && modal) closeBtn.addEventListener('click', () => closeModal(modal));
  if (cancelBtn && modal) cancelBtn.addEventListener('click', () => closeModal(modal));

  if (loanSelect) {
    loanSelect.addEventListener('change', (e) => onLoanSelected(e.target.value));
  }

  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      await submitPayment();
    });
  }

  // Check URL query parameters for pre-selected loan_id
  const urlParams = new URLSearchParams(window.location.search);
  const targetLoanId = urlParams.get('loan_id');
  if (targetLoanId) {
    openPaymentModal(targetLoanId);
  }
});

async function loadPayments() {
  try {
    const res = await fetch('/api/payments');
    const json = await res.json();

    if (!json.success) {
      showToast(json.error || "Failed to load payments history", "error");
      return;
    }

    renderPaymentsTable(json.payments);
  } catch (err) {
    console.error("Error loading payments:", err);
  }
}

function renderPaymentsTable(payments) {
  const tbody = document.getElementById('payments-table-body');
  if (!tbody) return;

  if (!payments || payments.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; color:var(--text-muted);">No payment transactions recorded yet.</td></tr>';
    return;
  }

  tbody.innerHTML = payments.map(p => `
    <tr>
      <td><strong>#${p.id}</strong></td>
      <td><strong style="cursor:pointer;" onclick="window.location.href='/loans.html?id=${p.loan_id}'">Loan #${p.loan_id}</strong></td>
      <td><strong style="color:var(--text-primary);">${escapeHtml(p.customer_name)}</strong></td>
      <td>${p.payment_date}</td>
      <td style="font-weight:700; color:var(--accent-emerald);">${formatINR(p.amount_paid)}</td>
      <td><span class="badge badge-completed">${p.payment_method}</span></td>
      <td style="color:var(--text-muted);">${escapeHtml(p.notes || '—')}</td>
    </tr>
  `).join('');
}

let loadedLoansMap = {};

async function openPaymentModal(preselectLoanId = null) {
  try {
    const res = await fetch('/api/loans?status=Active');
    const json = await res.json();
    const select = document.getElementById('payment-loan-id');

    if (!json.success || !select) return;

    if (json.loans.length === 0) {
      showToast("No active loans available for payment!", "error");
      return;
    }

    loadedLoansMap = {};
    select.innerHTML = '<option value="">-- Choose Active Loan --</option>' + json.loans.map(l => {
      loadedLoansMap[l.id] = l;
      return `<option value="${l.id}">Loan #${l.id} - ${escapeHtml(l.customer_name)} (Outstanding: ${formatINR(l.outstanding_balance)})</option>`;
    }).join('');

    const modal = document.getElementById('modal-payment');
    if (modal) modal.classList.add('active');

    if (preselectLoanId && loadedLoansMap[preselectLoanId]) {
      select.value = preselectLoanId;
      onLoanSelected(preselectLoanId);
    }
  } catch (err) {
    console.error("Error opening payment modal:", err);
  }
}

function closeModal(modal) {
  if (modal) modal.classList.remove('active');
}

async function onLoanSelected(loanId) {
  const infoBox = document.getElementById('payment-loan-info');
  const amountInput = document.getElementById('payment-amount');

  if (!loanId || !loadedLoansMap[loanId]) {
    if (infoBox) infoBox.style.display = 'none';
    return;
  }

  const l = loadedLoansMap[loanId];
  document.getElementById('info-cust-name').textContent = l.customer_name;
  document.getElementById('info-total-rep').textContent = formatINR(l.total_repayment);
  document.getElementById('info-outstanding').textContent = formatINR(l.outstanding_balance);

  // Fetch full details for schedule info
  try {
    const res = await fetch(`/api/loans/${loanId}`);
    const json = await res.json();
    if (json.success && json.loan && json.loan.schedule) {
      const pending = json.loan.schedule.find(s => s.status !== 'Paid');
      if (pending) {
        const dueAmt = pending.total_due - pending.amount_paid;
        document.getElementById('info-next-due').textContent = formatINR(dueAmt) + ` (Due: ${pending.due_date})`;
        if (amountInput) amountInput.value = dueAmt;
      } else {
        document.getElementById('info-next-due').textContent = formatINR(l.outstanding_balance);
        if (amountInput) amountInput.value = l.outstanding_balance;
      }
    }
  } catch (err) {
    console.error("Error loading schedule item for payment auto-fill:", err);
  }

  if (infoBox) infoBox.style.display = 'block';
}

async function submitPayment() {
  const loan_id = document.getElementById('payment-loan-id').value;
  const amount_paid = document.getElementById('payment-amount').value;
  const payment_method = document.getElementById('payment-method').value;
  const payment_date = document.getElementById('payment-date').value;
  const notes = document.getElementById('payment-notes').value.trim();

  if (!loan_id || !amount_paid) {
    showToast("Please select loan and payment amount.", "error");
    return;
  }

  const payload = {
    loan_id: parseInt(loan_id),
    amount_paid: parseFloat(amount_paid),
    payment_method,
    payment_date,
    notes
  };

  try {
    const res = await fetch('/api/payments', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const json = await res.json();

    if (json.success) {
      showToast("Payment recorded successfully! Repayment schedule & loan status updated.");
      closeModal(document.getElementById('modal-payment'));
      loadPayments();
    } else {
      showToast(json.error || "Failed to record payment", "error");
    }
  } catch (err) {
    console.error("Error submitting payment:", err);
    showToast("Server error recording payment", "error");
  }
}
