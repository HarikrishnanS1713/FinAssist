/**
 * FinAssist - Dashboard UI Handler
 * Fetches dashboard summary API and populates KPIs, recent customers, recent loans, upcoming, and overdue tables.
 */

document.addEventListener('DOMContentLoaded', () => {
  loadDashboardData();
});

async function loadDashboardData() {
  try {
    const res = await fetch('/api/dashboard');
    const json = await res.json();

    if (!json.success) {
      showToast(json.error || "Failed to load dashboard metrics", "error");
      return;
    }

    const d = json.data;

    // Update KPI Cards
    document.getElementById('kpi-total-customers').textContent = d.total_customers;
    document.getElementById('kpi-active-loans').textContent = d.active_loans;
    document.getElementById('kpi-total-lent').textContent = formatINR(d.total_amount_lent);
    document.getElementById('kpi-total-repaid').textContent = formatINR(d.total_amount_repaid);
    document.getElementById('kpi-total-outstanding').textContent = formatINR(d.total_outstanding);
    document.getElementById('kpi-expected-interest').textContent = formatINR(d.total_interest_expected);
    document.getElementById('kpi-todays-collections').textContent = formatINR(d.todays_collections);

    // Overdue Table
    renderOverdueTable(d.overdue_payments);

    // Upcoming Table
    renderUpcomingTable(d.upcoming_payments);

    // Recent Loans
    renderRecentLoansTable(d.recent_loans);

    // Recent Customers
    renderRecentCustomersTable(d.recent_customers);

  } catch (err) {
    console.error("Dashboard error:", err);
    showToast("Server connection error while loading dashboard", "error");
  }
}

function renderOverdueTable(items) {
  const tbody = document.getElementById('table-overdue-payments');
  if (!tbody) return;
  if (!items || items.length === 0) {
    tbody.innerHTML = '<tr><td colspan="4" style="text-align:center; color:var(--text-muted);">No overdue payments! 🎉</td></tr>';
    return;
  }
  tbody.innerHTML = items.map(item => `
    <tr>
      <td><strong style="color:var(--text-primary);">${escapeHtml(item.customer_name)}</strong><br/><small style="color:var(--text-muted);">${escapeHtml(item.customer_phone)}</small></td>
      <td style="color:var(--accent-rose); font-weight:600;">${item.due_date}</td>
      <td style="font-weight:700;">${formatINR(item.total_due - item.amount_paid)}</td>
      <td><span class="badge badge-overdue">Overdue</span></td>
    </tr>
  `).join('');
}

function renderUpcomingTable(items) {
  const tbody = document.getElementById('table-upcoming-payments');
  if (!tbody) return;
  if (!items || items.length === 0) {
    tbody.innerHTML = '<tr><td colspan="4" style="text-align:center; color:var(--text-muted);">No upcoming payments scheduled</td></tr>';
    return;
  }
  tbody.innerHTML = items.map(item => `
    <tr>
      <td><strong style="color:var(--text-primary);">${escapeHtml(item.customer_name)}</strong><br/><small style="color:var(--text-muted);">${escapeHtml(item.customer_phone)}</small></td>
      <td>${item.due_date}</td>
      <td style="font-weight:700;">${formatINR(item.total_due - item.amount_paid)}</td>
      <td><span class="badge badge-pending">Pending</span></td>
    </tr>
  `).join('');
}

function renderRecentLoansTable(loans) {
  const tbody = document.getElementById('table-recent-loans');
  if (!tbody) return;
  if (!loans || loans.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; color:var(--text-muted);">No loans recorded yet</td></tr>';
    return;
  }
  tbody.innerHTML = loans.map(l => `
    <tr>
      <td><strong>#${l.id}</strong></td>
      <td>${escapeHtml(l.customer_name)}</td>
      <td>${formatINR(l.principal)}</td>
      <td style="font-weight:700;">${formatINR(l.outstanding_balance)}</td>
      <td><span class="badge badge-${l.status.toLowerCase()}">${l.status}</span></td>
    </tr>
  `).join('');
}

function renderRecentCustomersTable(custs) {
  const tbody = document.getElementById('table-recent-customers');
  if (!tbody) return;
  if (!custs || custs.length === 0) {
    tbody.innerHTML = '<tr><td colspan="4" style="text-align:center; color:var(--text-muted);">No customers added yet</td></tr>';
    return;
  }
  tbody.innerHTML = custs.map(c => `
    <tr>
      <td>#${c.id}</td>
      <td><strong style="color:var(--text-primary);">${escapeHtml(c.full_name)}</strong></td>
      <td>${escapeHtml(c.phone)}</td>
      <td style="color:var(--text-muted);">${c.date_added}</td>
    </tr>
  `).join('');
}
