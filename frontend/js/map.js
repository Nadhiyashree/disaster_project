/**
 * map.js
 * ======
 * Leaflet map module for the Disaster Response Dashboard (Phase 2).
 * Visually communicates priority, confidence, and freshness on map popups.
 */

(function () {
  'use strict';

  let _map = null;
  let _markerLayer = null;
  let _initialized = false;

  const PRIORITY_COLOURS = {
    'Critical': '#ef4444',
    'High':     '#f97316',
    'Medium':   '#f59e0b',
    'Low':      '#3b82f6',
  };

  const INCIDENT_COLOURS = {
    'Road Flooding':       '#22d3ee',
    'Structural Damage':   '#f87171',
    'Power Outage':        '#fcd34d',
    'Medical Emergency':   '#ef4444',
    'Evacuation Needed':   '#fb923c',
    'Water Contamination': '#93c5fd',
  };

  function priorityColour(prio) {
    return PRIORITY_COLOURS[prio] || '#3b82f6';
  }

  function incidentColour(type) {
    return INCIDENT_COLOURS[type] || '#94a3b8';
  }

  function makeIcon(report) {
    const fill = incidentColour(report.incident_type);
    const ring = priorityColour(report.priority_category);
    const isCritical = report.priority_category === 'Critical';
    
    const svg = `
      <svg xmlns="http://www.w3.org/2000/svg" width="${isCritical ? 28 : 24}" height="${isCritical ? 34 : 30}" viewBox="0 0 24 30">
        <circle cx="12" cy="12" r="${isCritical ? 11 : 9}" fill="${fill}" fill-opacity="0.25" stroke="${ring}" stroke-width="${isCritical ? 3 : 2}"/>
        <circle cx="12" cy="12" r="5" fill="${ring}"/>
        <line x1="12" y1="21" x2="12" y2="29" stroke="${ring}" stroke-width="2"/>
      </svg>`;

    return L.divIcon({
      html: svg,
      className: isCritical ? 'critical-marker-pulse' : '',
      iconSize: [28, 34],
      iconAnchor: [14, 33],
      popupAnchor: [0, -32],
    });
  }

  function buildPopup(report) {
    const prioBadge = `<span class="badge badge-prio-${(report.priority_category || 'low').toLowerCase()}">${report.priority_category || 'Low'} (${report.priority_score || 0})</span>`;
    const confBadge = `<span class="badge badge-conf-${(report.confidence_category || 'low').toLowerCase().replace(' ', '-')}">${report.confidence_category || 'Low'} (${report.confidence_score || 0})</span>`;
    const freshBadge = `<span class="badge badge-fresh-${(report.freshness_state || 'unknown').toLowerCase()}">${report.freshness_state || 'Unknown'}</span>`;

    return `
      <div class="popup-title" style="display:flex;justify-content:space-between;align-items:center;">
        <span>🚨 <strong>${escapeHtml(report.report_id)}</strong></span>
        <span style="font-size:11px;color:#94a3b8;">${escapeHtml(report.zone)}</span>
      </div>
      <div class="popup-row">
        <span class="popup-label">Incident</span>
        <span class="popup-value">${escapeHtml(report.incident_type)}</span>
      </div>
      <div class="popup-row">
        <span class="popup-label">Priority</span>
        <span class="popup-value">${prioBadge}</span>
      </div>
      <div class="popup-row">
        <span class="popup-label">Confidence</span>
        <span class="popup-value">${confBadge}</span>
      </div>
      <div class="popup-row">
        <span class="popup-label">Freshness</span>
        <span class="popup-value">${freshBadge}</span>
      </div>
      <div class="popup-row">
        <span class="popup-label">Status</span>
        <span class="popup-value">${escapeHtml(report.status)}</span>
      </div>
      <div style="margin-top:10px;padding-top:8px;border-top:1px solid #1e293b;display:flex;justify-content:space-between;align-items:center;">
        <button class="btn btn-secondary btn-sm" onclick="window.viewReportDetails('${report.report_id}')" style="width:100%;justify-content:center;">
          📋 View Details
        </button>
      </div>`;
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function initMap(containerId) {
    if (_initialized) return;
    const container = document.getElementById(containerId);
    if (!container) {
      console.error('[map.js] Container not found:', containerId);
      return;
    }

    // Log container size for diagnostics
    const rect = container.getBoundingClientRect();
    console.log('[map.js] Container size at init:', rect.width, 'x', rect.height);

    try {
      _map = L.map(containerId, {
        center: [28.63, 77.22],
        zoom: 11,
        zoomControl: true,
        attributionControl: true,
        preferCanvas: false,
      });

      // Dark tile layer — Stadia Alidade Smooth Dark (free, no API key needed)
      const darkTiles = L.tileLayer(
        'https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/{z}/{x}/{y}{r}.png',
        {
          attribution: '&copy; <a href="https://stadiamaps.com/">Stadia Maps</a> &copy; <a href="https://openmaptiles.org/">OpenMapTiles</a> &copy; OpenStreetMap contributors',
          maxZoom: 20,
        }
      );

      // Fallback: OSM standard (always free, no key)
      const osmFallback = L.tileLayer(
        'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
        {
          attribution: '&copy; OpenStreetMap contributors',
          maxZoom: 19,
        }
      );

      // Try dark tiles first; if any tile errors occur, swap to OSM fallback
      let usingFallback = false;
      darkTiles.on('tileerror', function () {
        if (usingFallback) return;
        usingFallback = true;
        console.warn('[map.js] Dark tiles unavailable, switching to OSM fallback');
        _map.removeLayer(darkTiles);
        osmFallback.addTo(_map);
      });

      darkTiles.addTo(_map);
      _markerLayer = L.layerGroup().addTo(_map);
      _initialized = true;

      // Multiple invalidateSize calls to handle CSS layout settling
      setTimeout(() => { if (_map) { _map.invalidateSize(true); } }, 200);
      setTimeout(() => { if (_map) { _map.invalidateSize(true); } }, 600);
      setTimeout(() => { if (_map) { _map.invalidateSize(true); } }, 1200);

      console.log('[map.js] Map initialized successfully');
    } catch (err) {
      console.error('[map.js] Failed to initialize map:', err);
    }
  }

  function clearMarkers() {
    if (_markerLayer) _markerLayer.clearLayers();
  }

  function renderMarkers(reports) {
    if (!_initialized || !_markerLayer) return;
    clearMarkers();

    let count = 0;
    for (const report of reports) {
      const lat = parseFloat(report.latitude);
      const lng = parseFloat(report.longitude);

      if (!isFinite(lat) || !isFinite(lng)) continue;
      if (lat < -90 || lat > 90 || lng < -180 || lng > 180) continue;

      const icon = makeIcon(report);
      const marker = L.marker([lat, lng], { icon, alt: report.report_id });

      marker.bindPopup(buildPopup(report), {
        maxWidth: 300,
        className: 'dark-popup',
      });

      marker.on('popupopen', () => {
        document.dispatchEvent(new CustomEvent('mapMarkerSelected', {
          detail: { reportId: report.report_id },
        }));
      });

      _markerLayer.addLayer(marker);
      count++;
    }

    if (count > 0 && _map) {
      setTimeout(() => {
        invalidateSize();
        fitMarkers();
      }, 200);
    }
  }

  function fitMarkers() {
    if (!_map || !_markerLayer) return;
    const layers = _markerLayer.getLayers();
    if (layers.length === 0) return;
    const group = L.featureGroup(layers);
    _map.fitBounds(group.getBounds(), { padding: [30, 30], maxZoom: 14 });
  }

  function invalidateSize() {
    if (_map) _map.invalidateSize();
  }

  window.MapModule = {
    initMap,
    clearMarkers,
    renderMarkers,
    fitMarkers,
    invalidateSize,
    get initialized() { return _initialized; },
  };
})();
