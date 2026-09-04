/**
 * api.js
 * ======
 * Centralised API client for the Disaster Response Dashboard (Phase 2).
 */

const API_BASE_URL = window.location.origin;
const FETCH_TIMEOUT_MS = 15_000;

async function apiFetch(path, options = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
  const url = `${API_BASE_URL}${path}`;

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    clearTimeout(timer);

    if (!response.ok) {
      let detail = `HTTP ${response.status}`;
      try {
        const body = await response.json();
        detail = body.detail || detail;
      } catch (_) {}
      const err = new Error(detail);
      err.status = response.status;
      throw err;
    }

    return await response.json();
  } catch (err) {
    clearTimeout(timer);
    if (err.name === 'AbortError') {
      const timeout = new Error('Request timed out. Please try again.');
      timeout.status = 0;
      throw timeout;
    }
    throw err;
  }
}

function buildQuery(params = {}) {
  const qs = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== null && value !== undefined && value !== '') {
      qs.append(key, String(value));
    }
  }
  const str = qs.toString();
  return str ? `?${str}` : '';
}

// ── Public API ──────────────────────────────────────────────────────────────

async function getHealth() {
  return apiFetch('/api/health');
}

async function getReports(params = {}) {
  const qs = buildQuery(params);
  return apiFetch(`/api/reports${qs}`);
}

async function getReport(reportId) {
  return apiFetch(`/api/reports/${encodeURIComponent(reportId)}`);
}

async function getPriorityReports(params = {}) {
  const qs = buildQuery(params);
  return apiFetch(`/api/reports/priority${qs}`);
}

async function getStaleReports(params = {}) {
  const qs = buildQuery(params);
  return apiFetch(`/api/reports/stale${qs}`);
}

async function getConflictReports(params = {}) {
  const qs = buildQuery(params);
  return apiFetch(`/api/reports/conflicts${qs}`);
}

async function verifyReport(reportId, status, notes = null) {
  return apiFetch(`/api/reports/${encodeURIComponent(reportId)}/verify`, {
    method: 'POST',
    body: JSON.stringify({ status, notes }),
  });
}

async function getDashboardStats() {
  return apiFetch('/api/dashboard/stats');
}

async function getMetrics() {
  return apiFetch('/api/metrics');
}

// Export global API object
window.API = {
  getHealth,
  getReports,
  getReport,
  getPriorityReports,
  getStaleReports,
  getConflictReports,
  verifyReport,
  getDashboardStats,
  getMetrics,
};
