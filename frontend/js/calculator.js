/**
 * FinAssist - Standalone Loan Calculator Script
 * Sends request to backend /api/calculate-loan and updates interactive UI metrics and repayment schedule preview.
 */

document.addEventListener('DOMContentLoaded', () => {
  const startDate = document.getElementById('calc-start-date');
  if (startDate) {
    startDate.value = new Date().toISOString().split('T')[0];
  }

  const form = document.getElementById('calc-form');
  if (form) {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      runCalculation();
    });
  }

  // Run initial calculation on page load
  runCalculation();
});

async function runCalculation() {
  const principal = parseFloat(document.getElementById('calc-principal').value) || 0;
  const rate = parseFloat(document.getElementById('calc-rate').value) || 0;
  const itype = document.getElementById('calc-interest-type').value;
  const duration = parseInt(document.getElementById('calc-duration').value) || 0;
  const start_date = document.getElementById('calc-start-date').value;
  const freq = document.getElementById('calc-frequency').value;

  if (principal <= 0 || duration <= 0) {
    showToast("Principal and duration must be greater than zero.", "error");
    return;
  }

  try {
    const res = await fetch('/api/calculate-loan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        principal, interest_rate: rate, interest_type: itype,
        duration_months: duration, start_date, payment_frequency: freq
      })
    });
    const json = await res.json();

    if (!json.success) {
      showToast(json.error || "Calculation failed", "error");
      return;
    }

    renderCalcResults(json.calculation);
  } catch (err) {
    console.error("Calculation error:", err);
  }
}

function renderCalcResults(c) {
  document.getElementById('out-principal').textContent = formatINR(c.principal);
  document.getElementById('out-total-interest').textContent = formatINR(c.total_interest);
  document.getElementById('out-total-repayment').textContent = formatINR(c.total_repayment);
  document.getElementById('out-monthly').textContent = formatINR(c.monthly_payment);
  document.getElementById('out-weekly').textContent = formatINR(c.weekly_payment);
  document.getElementById('out-daily').textContent = formatINR(c.daily_payment);
  document.getElementById('out-num-payments').textContent = c.num_payments;
  document.getElementById('out-end-date').textContent = c.end_date;

  const tbody = document.getElementById('calc-schedule-body');
  if (!tbody) return;

  if (!c.schedule || c.schedule.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; color:var(--text-muted);">No schedule generated</td></tr>';
    return;
  }

  tbody.innerHTML = c.schedule.map(item => `
    <tr>
      <td><strong>${item.payment_number}</strong></td>
      <td>${item.due_date}</td>
      <td>${formatINR(item.principal_component)}</td>
      <td>${formatINR(item.interest_component)}</td>
      <td style="font-weight:700; color:var(--text-primary);">${formatINR(item.total_due)}</td>
      <td>${formatINR(item.remaining_balance)}</td>
    </tr>
  `).join('');
}
