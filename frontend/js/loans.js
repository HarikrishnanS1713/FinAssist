/**
 * FinAssist - Loan Management Controller
 * Handles loans listing, loan creation modal, live preview calculation, and repayment schedule viewer.
 */

document.addEventListener('DOMContentLoaded', () => {
  loadLoans();

  // Set today as default start date in form
  const startDateInput = document.getElementById('loan-start-date');
  if (startDateInput) {
    startDateInput.value = new Date().toISOString().split('T')[0];
  }

  // Filter Handler
  const statusFilter = document.getElementById('loan-status-filter');
  if (statusFilter) {
    statusFilter.addEventListener('change', (e) => loadLoans(e.target.value));
  }

  // Modal handlers
  const createBtn = document.getElementById('btn-create-loan');
  const modal = document.getElementById('modal-loan');
  const closeBtn = document.getElementById('btn-close-loan-modal');
  const cancelBtn = document.getElementById('btn-cancel-loan-modal');
  const form = document.getElementById('form-loan');

  if (createBtn && modal) {
    createBtn.addEventListener('click', () => openLoanModal());
  }

  if (closeBtn && modal) closeBtn.addEventListener('click', () => closeModal(modal));
  if (cancelBtn && modal) cancelBtn.addEventListener('click', () => closeModal(modal));

  const closeScheduleBtn = document.getElementById('btn-close-schedule-modal');
  const scheduleModal = document.getElementById('modal-schedule');
  if (closeScheduleBtn && scheduleModal) closeScheduleBtn.addEventListener('click', () => closeModal(scheduleModal));

  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      await submitNewLoan();
    });
  }

  // Live calculation preview listeners
  ['loan-principal', 'loan-rate', 'loan-interest-type', 'loan-duration', 'loan-frequency'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.addEventListener('input', updateLivePreview);
  });

  // Check URL query for loan ID
  const urlParams = new URLSearchParams(window.location.search);
  const targetId = urlParams.get('id');
  if (targetId) {
    viewSchedule(targetId);
  }
});

async function loadLoans(status = '') {
  try {
    const url = status ? `/api/loans?status=${encodeURIComponent(status)}` : '/api/loans';
    const res = await fetch(url);
    const json = await res.json();

    if (!json.success) {
      showToast(json.error || "Failed to load loans", "error");
      return;
    }

    renderLoansTable(json.loans);
  } catch (err) {
    console.error("Error loading loans:", err);
  }
}

function renderLoansTable(loans) {
  const tbody = document.getElementById('loans-table-body');
  if (!tbody) return;

  if (!loans || loans.length === 0) {
    tbody.innerHTML = '<tr><td colspan="10" style="text-align:center; color:var(--text-muted);">No loans found. Click "Issue New Loan" to get started.</td></tr>';
    return;
  }

  tbody.innerHTML = loans.map(l => `
    <tr>
      <td><strong>#${l.id}</strong></td>
      <td><strong style="color:var(--text-primary); cursor:pointer;" onclick="window.location.href='/customers.html?id=${l.customer_id}'">${escapeHtml(l.customer_name)}</strong></td>
      <td>${formatINR(l.principal)}</td>
      <td>${l.interest_rate}% (${l.interest_type.toUpperCase()})</td>
      <td>${l.duration_months} M (${l.payment_frequency})</td>
      <td>${formatINR(l.total_repayment)}</td>
      <td style="color:var(--accent-emerald);">${formatINR(l.amount_paid)}</td>
      <td style="font-weight:700; color:${l.outstanding_balance > 0 ? 'var(--accent-rose)' : 'var(--accent-emerald)'};">${formatINR(l.outstanding_balance)}</td>
      <td><span class="badge badge-${l.status.toLowerCase()}">${l.status}</span></td>
      <td>
        <div style="display:flex; gap:0.4rem;">
          <button class="btn btn-secondary btn-sm" onclick="viewSchedule(${l.id})">Schedule</button>
          <button class="btn btn-primary btn-sm" onclick="window.location.href='/payments.html?loan_id=${l.id}'">Pay</button>
          <button class="btn btn-danger btn-sm" onclick="confirmDeleteLoan(${l.id})">Delete</button>
        </div>
      </td>
    </tr>
  `).join('');
}

async function openLoanModal() {
  // Populate customers dropdown
  try {
    const res = await fetch('/api/customers');
    const json = await res.json();
    const select = document.getElementById('loan-customer-id');

    if (json.success && select) {
      if (json.customers.length === 0) {
        showToast("Please add at least one customer before creating a loan!", "error");
        window.location.href = '/customers.html';
        return;
      }
      select.innerHTML = '<option value="">-- Choose Customer --</option>' + json.customers.map(c => `
        <option value="${c.id}">${escapeHtml(c.full_name)} (Phone: ${escapeHtml(c.phone)})</option>
      `).join('');
    }

    const modal = document.getElementById('modal-loan');
    if (modal) modal.classList.add('active');
    updateLivePreview();
  } catch (err) {
    console.error("Error loading customer dropdown:", err);
  }
}

function closeModal(modal) {
  if (modal) modal.classList.remove('active');
}

async function updateLivePreview() {
  const principal = parseFloat(document.getElementById('loan-principal').value) || 0;
  const rate = parseFloat(document.getElementById('loan-rate').value) || 0;
  const itype = document.getElementById('loan-interest-type').value;
  const duration = parseInt(document.getElementById('loan-duration').value) || 0;
  const freq = document.getElementById('loan-frequency').value;
  const previewBox = document.getElementById('loan-preview-box');

  if (principal <= 0 || duration <= 0) {
    if (previewBox) previewBox.style.display = 'none';
    return;
  }

  try {
    const res = await fetch('/api/calculate-loan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        principal, interest_rate: rate, interest_type: itype,
        duration_months: duration, payment_frequency: freq
      })
    });
    const json = await res.json();
    if (json.success && previewBox) {
      const c = json.calculation;
      document.getElementById('prev-interest').textContent = formatINR(c.total_interest);
      document.getElementById('prev-repayment').textContent = formatINR(c.total_repayment);
      document.getElementById('prev-installment').textContent = formatINR(c.periodic_payment) + ` (${c.payment_frequency})`;
      previewBox.style.display = 'block';
    }
  } catch (err) {
    console.error("Preview error:", err);
  }
}

async function submitNewLoan() {
  const customer_id = document.getElementById('loan-customer-id').value;
  const principal = document.getElementById('loan-principal').value;
  const interest_rate = document.getElementById('loan-rate').value;
  const interest_type = document.getElementById('loan-interest-type').value;
  const duration_months = document.getElementById('loan-duration').value;
  const start_date = document.getElementById('loan-start-date').value;
  const payment_frequency = document.getElementById('loan-frequency').value;

  if (!customer_id || !principal || !start_date) {
    showToast("Please fill in all required fields.", "error");
    return;
  }

  const payload = {
    customer_id: parseInt(customer_id),
    principal: parseFloat(principal),
    interest_rate: parseFloat(interest_rate),
    interest_type,
    duration_months: parseInt(duration_months),
    start_date,
    payment_frequency
  };

  try {
    const res = await fetch('/api/loans', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const json = await res.json();

    if (json.success) {
      showToast("Loan issued and repayment schedule generated!");
      closeModal(document.getElementById('modal-loan'));
      loadLoans();
      viewSchedule(json.loan.id);
    } else {
      showToast(json.error || "Failed to create loan", "error");
    }
  } catch (err) {
    console.error("Error creating loan:", err);
    showToast("Server error issuing loan", "error");
  }
}

async function confirmDeleteLoan(id) {
  if (confirm(`Delete Loan #${id}? This will remove all associated schedule items and payment history.`)) {
    try {
      const res = await fetch(`/api/loans/${id}`, { method: 'DELETE' });
      const json = await res.json();
      if (json.success) {
        showToast("Loan deleted.");
        loadLoans();
      } else {
        showToast(json.error || "Failed to delete loan", "error");
      }
    } catch (err) {
      console.error("Delete error:", err);
    }
  }
}

async function viewSchedule(loanId) {
  try {
    const res = await fetch(`/api/loans/${loanId}`);
    const json = await res.json();
    if (!json.success || !json.loan) {
      showToast(json.error || "Loan schedule not found", "error");
      return;
    }

    const loan = json.loan;
    document.getElementById('modal-schedule-title').textContent = `Repayment Schedule - Loan #${loan.id} (${escapeHtml(loan.customer_name)})`;

    const body = document.getElementById('schedule-modal-body');
    if (!body) return;

    body.innerHTML = `
      <div style="display:grid; grid-template-columns: repeat(4, 1fr); gap: 0.75rem; margin-bottom: 1.25rem; background: var(--bg-card); padding: 1rem; border-radius: var(--radius-md); font-size: 0.85rem;">
        <div>Principal: <strong style="color:#fff;">${formatINR(loan.principal)}</strong></div>
        <div>Interest: <strong style="color:#fff;">${loan.interest_rate}% (${loan.interest_type})</strong></div>
        <div>Total Repayment: <strong style="color:#fff;">${formatINR(loan.total_repayment)}</strong></div>
        <div>Outstanding: <strong style="color:var(--accent-rose);">${formatINR(loan.outstanding_balance)}</strong></div>
      </div>

      <div class="table-responsive" style="max-height: 400px; overflow-y: auto;">
        <table class="data-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Due Date</th>
              <th>Principal Comp.</th>
              <th>Interest Comp.</th>
              <th>Total Due</th>
              <th>Amount Paid</th>
              <th>Remaining</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            ${loan.schedule.map(item => `
              <tr>
                <td><strong>${item.payment_number}</strong></td>
                <td>${item.due_date}</td>
                <td>${formatINR(item.principal_component)}</td>
                <td>${formatINR(item.interest_component)}</td>
                <td style="font-weight:700;">${formatINR(item.total_due)}</td>
                <td style="color:var(--accent-emerald);">${formatINR(item.amount_paid)}</td>
                <td>${formatINR(item.remaining_balance)}</td>
                <td><span class="badge badge-${item.status.toLowerCase().replace(' ', '')}">${item.status}</span></td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    `;

    const modal = document.getElementById('modal-schedule');
    if (modal) modal.classList.add('active');

  } catch (err) {
    console.error("Error viewing schedule:", err);
  }
}
