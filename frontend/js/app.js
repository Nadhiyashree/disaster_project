/**
 * app.js
 * ======
 * Global application utilities and shared UI behaviours.
 *
 * Responsibilities:
 *  - Role selector
 *  - System status (health check)
 *  - Last-updated clock
 *  - Toast notification system
 *  - Common DOM helpers
 *  - Navigation helpers
 */

(function () {
  'use strict';

  // ── Toast System ───────────────────────────────────────────────────────────

  let _toastContainer = null;

  function getToastContainer() {
    if (_toastContainer) return _toastContainer;
    _toastContainer = document.createElement('div');
    _toastContainer.className = 'toast-container';
    _toastContainer.setAttribute('aria-live', 'polite');
    document.body.appendChild(_toastContainer);
    return _toastContainer;
  }

  /**
   * Show a toast notification.
   * @param {string} message
   * @param {'info'|'success'|'warning'|'error'} type
   * @param {number} durationMs
   */
  function showToast(message, type = 'info', durationMs = 3500) {
    const container = getToastContainer();
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    toast.setAttribute('role', 'status');
    container.appendChild(toast);
    setTimeout(() => {
      toast.style.transition = 'opacity .3s';
      toast.style.opacity = '0';
      setTimeout(() => toast.remove(), 350);
    }, durationMs);
  }

  // ── Role Selector ──────────────────────────────────────────────────────────

  const ROLES = ['Responder', 'City Official', 'Coordinator'];
  const ROLE_KEY = 'drp_selected_role';

  function initRoleSelector() {
    const select = document.getElementById('role-select');
    if (!select) return;

    // Populate options if empty
    if (select.options.length === 0) {
      ROLES.forEach(role => {
        const opt = document.createElement('option');
        opt.value = role;
        opt.textContent = role;
        select.appendChild(opt);
      });
    }

    // Restore saved role
    const saved = localStorage.getItem(ROLE_KEY);
    if (saved && ROLES.includes(saved)) select.value = saved;

    select.addEventListener('change', () => {
      const role = select.value;
      localStorage.setItem(ROLE_KEY, role);
      showToast(`Role switched to: ${role}`, 'info', 2000);
      document.dispatchEvent(new CustomEvent('roleChanged', { detail: { role } }));
    });
  }

  function getCurrentRole() {
    const select = document.getElementById('role-select');
    return select ? select.value : localStorage.getItem(ROLE_KEY) || 'Responder';
  }

  // ── System Status (health check) ───────────────────────────────────────────

  const STATUS_PILL_ID = 'system-status';
  let _healthCheckInterval = null;

  async function checkHealth() {
    const pill = document.getElementById(STATUS_PILL_ID);
    if (!pill) return;

    try {
      const data = await window.API.getHealth();
      if (data.status === 'ok') {
        setStatusOnline(pill);
      } else {
        setStatusOffline(pill, 'Degraded');
      }
    } catch (_) {
      setStatusOffline(pill, 'Offline');
    }
  }

  function setStatusOnline(pill) {
    pill.className = 'status-pill';
    pill.innerHTML = '<span class="dot"></span> System Online';
  }

  function setStatusOffline(pill, label) {
    pill.className = 'status-pill offline';
    pill.innerHTML = `<span class="dot"></span> ${label}`;
  }

  function startHealthPolling(intervalMs = 60_000) {
    checkHealth();
    if (_healthCheckInterval) clearInterval(_healthCheckInterval);
    _healthCheckInterval = setInterval(checkHealth, intervalMs);
  }

  // ── Last-updated display ───────────────────────────────────────────────────

  function updateLastUpdatedDisplay() {
    const el = document.getElementById('last-updated-time');
    if (el) el.textContent = new Date().toLocaleTimeString();
  }

  // ── DOM Helpers ────────────────────────────────────────────────────────────

  function $(selector, context = document) {
    return context.querySelector(selector);
  }

  function $$(selector, context = document) {
    return Array.from(context.querySelectorAll(selector));
  }

  function setTextContent(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
  }

  function show(el) {
    if (el) el.style.display = '';
  }

  function hide(el) {
    if (el) el.style.display = 'none';
  }

  function formatTimestamp(isoString) {
    if (!isoString) return '—';
    try {
      return new Date(isoString).toLocaleString();
    } catch (_) {
      return isoString;
    }
  }

  function formatRelativeTime(isoString) {
    if (!isoString) return '—';
    const now = Date.now();
    const then = new Date(isoString).getTime();
    const diffMs = now - then;
    const diffMin = Math.round(diffMs / 60_000);

    if (diffMin < 1) return 'Just now';
    if (diffMin < 60) return `${diffMin}m ago`;
    const diffH = Math.round(diffMin / 60);
    if (diffH < 24) return `${diffH}h ago`;
    const diffD = Math.round(diffH / 24);
    return `${diffD}d ago`;
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  // ── Status → CSS class ─────────────────────────────────────────────────────

  function statusBadgeClass(status) {
    const map = {
      'Verified':     'badge-verified',
      'Pending':      'badge-pending',
      'Rejected':     'badge-rejected',
      'Needs Review': 'badge-needs-review',
    };
    return map[status] || 'badge-default';
  }

  function incidentPillClass(type) {
    const map = {
      'Road Flooding':        'incident-road-flooding',
      'Structural Damage':    'incident-structural-damage',
      'Power Outage':         'incident-power-outage',
      'Medical Emergency':    'incident-medical-emergency',
      'Evacuation Needed':    'incident-evacuation-needed',
      'Water Contamination':  'incident-water-contamination',
    };
    return map[type] || '';
  }

  // ── Initialisation ─────────────────────────────────────────────────────────

  function init() {
    initRoleSelector();
    startHealthPolling();
    updateLastUpdatedDisplay();
  }

  // Run when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // ── Exports ────────────────────────────────────────────────────────────────
  window.APP = {
    showToast,
    getCurrentRole,
    checkHealth,
    updateLastUpdatedDisplay,
    $,
    $$,
    setTextContent,
    show,
    hide,
    formatTimestamp,
    formatRelativeTime,
    escapeHtml,
    statusBadgeClass,
    incidentPillClass,
  };
})();
