/**
 * app.js
 * ======
 * Global application utilities, persistent navigation, role management,
 * confirmation modal, and shared UI behaviors for Phase 3.
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

  // ── Role Selector Persistence ──────────────────────────────────────────────

  const ROLES = ['Responder', 'City Official', 'Coordinator'];
  const ROLE_KEY = 'drp_selected_role';

  function initRoleSelector() {
    const select = document.getElementById('role-select');
    if (!select) return;

    if (select.options.length === 0) {
      ROLES.forEach(role => {
        const opt = document.createElement('option');
        opt.value = role;
        opt.textContent = role;
        select.appendChild(opt);
      });
    }

    const saved = localStorage.getItem(ROLE_KEY);
    if (saved && ROLES.includes(saved)) {
      select.value = saved;
    }

    select.addEventListener('change', () => {
      const role = select.value;
      localStorage.setItem(ROLE_KEY, role);
      showToast(`Role view switched to: ${role}`, 'info', 2000);
      document.dispatchEvent(new CustomEvent('roleChanged', { detail: { role } }));
    });
  }

  function getCurrentRole() {
    const select = document.getElementById('role-select');
    return select ? select.value : (localStorage.getItem(ROLE_KEY) || 'Responder');
  }

  // ── Navigation Bar Active Link Highlighting ───────────────────────────────

  function initNavHighlighting() {
    const navLinks = document.querySelectorAll('.nav-link');
    const path = window.location.pathname.toLowerCase();

    navLinks.forEach(link => {
      const href = link.getAttribute('href').toLowerCase();
      if (
        href === path ||
        (path === '/' && href === '/dashboard.html') ||
        (path.includes('dashboard') && href.includes('dashboard')) ||
        (path.includes('reports') && !path.includes('details') && href.includes('reports.html')) ||
        (path.includes('report-details') && href.includes('report-details')) ||
        (path.includes('analytics') && href.includes('analytics')) ||
        (path.includes('methodology') && href.includes('methodology'))
      ) {
        link.classList.add('active');
      } else {
        link.classList.remove('active');
      }
    });
  }

  // ── System Status (Health Check) ──────────────────────────────────────────

  const STATUS_PILL_ID = 'system-status';
  let _healthCheckInterval = null;

  async function checkHealth() {
    const pill = document.getElementById(STATUS_PILL_ID);
    if (!pill) return;

    try {
      const data = await window.API.getHealth();
      if (data && data.status === 'ok') {
        pill.className = 'status-pill';
        pill.innerHTML = '<span class="dot"></span> SYSTEM OPERATIONAL';
      } else {
        pill.className = 'status-pill offline';
        pill.innerHTML = '<span class="dot"></span> DEGRADED';
      }
    } catch (_) {
      pill.className = 'status-pill offline';
      pill.innerHTML = '<span class="dot"></span> BACKEND OFFLINE';
    }
  }

  function startHealthPolling(intervalMs = 45_000) {
    checkHealth();
    if (_healthCheckInterval) clearInterval(_healthCheckInterval);
    _healthCheckInterval = setInterval(checkHealth, intervalMs);
  }

  // ── Confirmation Modal Dialog ─────────────────────────────────────────────

  function showConfirmationModal({ title, message, confirmText = 'Confirm', onConfirm }) {
    let backdrop = document.getElementById('confirm-modal-backdrop');
    if (!backdrop) {
      backdrop = document.createElement('div');
      backdrop.id = 'confirm-modal-backdrop';
      backdrop.className = 'modal-backdrop';
      backdrop.innerHTML = `
        <div class="modal" style="max-width:480px;">
          <div class="modal-header">
            <span id="confirm-modal-title" class="modal-title">⚠️ Confirmation Required</span>
            <button id="confirm-modal-close" class="modal-close">✕</button>
          </div>
          <div class="modal-body">
            <p id="confirm-modal-msg" style="font-size:14px;color:var(--text-secondary);line-height:1.5;"></p>
            <div class="modal-confirm-actions">
              <button id="confirm-btn-cancel" class="btn btn-secondary">Cancel</button>
              <button id="confirm-btn-action" class="btn btn-primary">Proceed</button>
            </div>
          </div>
        </div>`;
      document.body.appendChild(backdrop);
    }

    document.getElementById('confirm-modal-title').textContent = title || 'Confirm Action';
    document.getElementById('confirm-modal-msg').textContent = message;

    const actionBtn = document.getElementById('confirm-btn-action');
    actionBtn.textContent = confirmText;

    const close = () => backdrop.classList.remove('open');

    document.getElementById('confirm-modal-close').onclick = close;
    document.getElementById('confirm-btn-cancel').onclick = close;

    actionBtn.onclick = async () => {
      close();
      if (onConfirm) await onConfirm();
    };

    backdrop.classList.add('open');
  }

  // ── DOM Helpers ────────────────────────────────────────────────────────────

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function statusBadgeClass(status) {
    const map = {
      'Verified':     'badge-verified',
      'Pending':      'badge-pending',
      'Rejected':     'badge-rejected',
      'Needs Review': 'badge-needs-review',
    };
    return map[status] || 'badge-default';
  }

  function formatTimestamp(isoString) {
    if (!isoString) return '—';
    try {
      return new Date(isoString).toLocaleString();
    } catch (_) {
      return isoString;
    }
  }

  // ── Initialisation ─────────────────────────────────────────────────────────

  function init() {
    initRoleSelector();
    initNavHighlighting();
    startHealthPolling();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  window.APP = {
    showToast,
    getCurrentRole,
    checkHealth,
    showConfirmationModal,
    escapeHtml,
    statusBadgeClass,
    formatTimestamp,
  };
})();
