import React, { useState, useEffect, useCallback } from 'react';
import { AlertTriangle, Filter, Search, ChevronUp, ChevronDown, RefreshCw, ShieldOff } from 'lucide-react';
import { useAuth } from '../store/AuthContext';
import { useSOC } from '../store/SOCContext';

// ── Constants ─────────────────────────────────────────────────────────────────
const SEVERITIES  = ['Critical', 'High', 'Medium', 'Low'];
const TIME_RANGES = ['Last 1h', 'Last 6h', 'Last 24h', '7 Days'];

const SEVERITY_STYLES = {
  Critical: { bg: '#EF444422', border: '#EF4444', color: '#EF4444' },
  High:     { bg: '#E5A86222', border: '#E5A862', color: '#E5A862' },
  Medium:   { bg: '#3B6FE322', border: '#3B6FE3', color: '#3B6FE3' },
  Low:      { bg: '#88C05722', border: '#88C057', color: '#88C057' },
};

// ── Field normaliser ──────────────────────────────────────────────────────────
// The triage agent can write various field shapes (OCSF, raw, custom).
// This maps any known variant to the shape this component expects.
function normaliseAlert(raw) {
  const ts = raw.timestamp || raw.time || raw.created_at || '';
  const timeLabel = ts
    ? new Date(ts).toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })
    : '—';

  return {
    id:       raw.alert_id   || raw.id        || `ALT-${Math.random().toString(36).slice(2,7).toUpperCase()}`,
    title:    raw.title      || raw.name      || raw.description || 'Unnamed Alert',
    severity: raw.severity   || raw.priority  || 'Low',
    source:   raw.source     || raw.log_source || raw.sensor     || 'Unknown',
    asset:    raw.asset      || raw.host       || raw.source_ip  || raw.src_ip || raw.device || '—',
    time:     timeLabel,
    mitre:    raw.mitre      || raw.mitre_technique || raw.technique_id || raw.mitre_ttp || '',
    agent:    raw.agent      || raw.assigned_agent  || raw.triage_agent || 'UNASSIGNED',
    // Advanced Metadata
    ftse_metrics: raw.raw_event?.unmapped?.time_series_math || {},
    description: raw.description || '',
    semantic_detail: raw.semantic_detail || '',
    vector_id: raw.vector_id || '',
    is_correlated: raw.is_correlated || false,
  };
}

// ── Sub-components ────────────────────────────────────────────────────────────
function SeverityBadge({ level }) {
  const s = SEVERITY_STYLES[level] || SEVERITY_STYLES['Low'];
  return (
    <span className="inline-flex items-center gap-1 text-xs font-bold terminal px-2 py-0.5 rounded"
      style={{ background: s.bg, border: `1px solid ${s.border}`, color: s.color }}>
      {level === 'Critical' && <span className="w-1.5 h-1.5 rounded-full animate-blink" style={{ background: s.color }} />}
      {level}
    </span>
  );
}

function SkeletonRow() {
  return (
    <div className="grid items-center px-4 py-3 border-b animate-shimmer"
      style={{ gridTemplateColumns: '100px 1fr 120px 80px 110px 130px 130px', borderColor: '#1F2937' }}>
      {[100, 200, 80, 50, 70, 90, 100].map((w, i) => (
        <div key={i} className="h-3 rounded" style={{ width: w, background: '#1F2937' }} />
      ))}
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────────────────────
export default function AlertQueue() {
  const { authenticatedFetch } = useAuth();
  const { setSelectedHost } = useSOC();

  const [alerts,       setAlerts]       = useState([]);
  const [loading,      setLoading]      = useState(true);
  const [error,        setError]        = useState(null);
  const [lastRefresh,  setLastRefresh]  = useState(null);

  const [activeSev,    setActiveSev]    = useState('All');
  const [activeSource, setActiveSource] = useState('All');
  const [timeRange,    setTimeRange]    = useState('Last 6h');
  const [search,       setSearch]       = useState('');
  const [sortDir,      setSortDir]      = useState('desc');
  const [selectedAlert, setSelectedAlert] = useState(null);

  // ── Fetch ────────────────────────────────────────────────────────────────
  const fetchAlerts = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await authenticatedFetch('http://localhost:8000/alerts');
      if (!res.ok) throw new Error(`HTTP ${res.status} — ${res.statusText}`);
      const raw = await res.json();
      const normalised = (Array.isArray(raw) ? raw : []).map(normaliseAlert);
      // Sort newest first by default
      normalised.sort((a, b) => b.time.localeCompare(a.time));
      setAlerts(normalised);
      setLastRefresh(new Date());
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [authenticatedFetch]);

  useEffect(() => { fetchAlerts(); }, [fetchAlerts]);

  // ── Derived values ────────────────────────────────────────────────────────
  const availableSources = ['All', ...new Set(alerts.map(a => a.source).filter(Boolean))];

  const filtered = alerts
    .filter(a =>
      (activeSev    === 'All' || a.severity === activeSev) &&
      (activeSource === 'All' || a.source   === activeSource) &&
      (!search || a.title.toLowerCase().includes(search.toLowerCase()) || a.asset.toLowerCase().includes(search.toLowerCase()))
    )
    .sort((a, b) => sortDir === 'desc' ? b.time.localeCompare(a.time) : a.time.localeCompare(b.time));

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="flex flex-col h-full" style={{ background: '#0B1117' }}>

      {/* Toolbar */}
      <div className="flex items-center gap-3 px-4 py-3 border-b flex-shrink-0"
        style={{ borderColor: '#1F2937', background: '#0d1117' }}>
        <AlertTriangle size={15} style={{ color: '#EF4444' }} />
        <span className="text-xs font-bold tracking-widest" style={{ color: '#E2E8F0' }}>ALERT QUEUE</span>
        <span className="ml-1 text-xs terminal px-2 py-0.5 rounded-full"
          style={{ background: '#EF444422', color: '#EF4444', border: '1px solid #EF444444' }}>
          {loading ? '…' : filtered.length}
        </span>

        {/* Search */}
        <div className="flex-1 relative ml-4">
          <Search size={12} className="absolute left-2.5 top-1/2 -translate-y-1/2" style={{ color: '#4B5563' }} />
          <input value={search} onChange={e => setSearch(e.target.value)}
            placeholder="Search alerts, hosts, IPs..."
            className="w-full text-xs py-1.5 pl-8 pr-3 rounded terminal focus:outline-none"
            style={{ background: '#111827', border: '1px solid #1F2937', color: '#9CA3AF' }} />
        </div>

        {/* Time Range */}
        <div className="flex items-center gap-1">
          {TIME_RANGES.map(t => (
            <button key={t} onClick={() => setTimeRange(t)}
              className="text-xs terminal px-2.5 py-1 rounded transition-all"
              style={{
                background: timeRange === t ? '#3B6FE322' : 'transparent',
                color:      timeRange === t ? '#3B6FE3'   : '#6B7280',
                border:    `1px solid ${timeRange === t ? '#3B6FE344' : 'transparent'}`,
              }}>
              {t}
            </button>
          ))}
        </div>

        {/* Refresh */}
        <button onClick={fetchAlerts} disabled={loading}
          className="p-1.5 rounded hover:bg-white/5 transition-colors"
          title={lastRefresh ? `Last: ${lastRefresh.toLocaleTimeString()}` : 'Refresh'}>
          <RefreshCw size={12} style={{ color: '#4B5563' }} className={loading ? 'animate-spin-slow' : ''} />
        </button>
      </div>

      {/* Filter Row */}
      <div className="flex items-center gap-2 px-4 py-2 border-b flex-shrink-0"
        style={{ borderColor: '#1F2937' }}>
        <Filter size={11} style={{ color: '#6B7280' }} />
        <span className="text-xs" style={{ color: '#6B7280' }}>Severity:</span>
        {['All', ...SEVERITIES].map(s => {
          const style = s !== 'All' ? SEVERITY_STYLES[s] : null;
          return (
            <button key={s} onClick={() => setActiveSev(s)}
              className="text-xs terminal px-2 py-0.5 rounded-full transition-all"
              style={{
                background: activeSev === s ? (style?.bg || '#FFFFFF11') : 'transparent',
                color:      activeSev === s ? (style?.color || '#E2E8F0') : '#6B7280',
                border:    `1px solid ${activeSev === s ? (style?.border || '#6B7280') : 'transparent'}`,
              }}>
              {s}
            </button>
          );
        })}
        <div className="w-px h-4 mx-2" style={{ background: '#1F2937' }} />
        <span className="text-xs" style={{ color: '#6B7280' }}>Source:</span>
        {availableSources.map(s => (
          <button key={s} onClick={() => setActiveSource(s)}
            className="text-xs terminal px-2 py-0.5 rounded transition-all"
            style={{
              background: activeSource === s ? '#FFFFFF11' : 'transparent',
              color:      activeSource === s ? '#E2E8F0'   : '#6B7280',
              border:    `1px solid ${activeSource === s ? '#374151' : 'transparent'}`,
            }}>
            {s}
          </button>
        ))}
      </div>

      {/* Table Header */}
      <div className="grid h-label px-4 py-2.5 border-b flex-shrink-0"
        style={{ gridTemplateColumns: '100px 1fr 120px 80px 110px 130px 130px', borderColor: '#1F2937', background: '#080d14' }}>
        <span>Severity</span>
        <span>Alert</span>
        <span>Asset</span>
        <span>Source</span>
        <div className="flex items-center gap-1 cursor-pointer" onClick={() => setSortDir(d => d === 'asc' ? 'desc' : 'asc')}>
          Time {sortDir === 'asc' ? <ChevronUp size={10} /> : <ChevronDown size={10} />}
        </div>
        <span>Mitre ATT&amp;CK</span>
        <span>Agent</span>
      </div>

      {/* Table Body */}
      <div className="flex-1 overflow-y-auto">

        {/* Loading skeletons */}
        {loading && Array.from({ length: 6 }).map((_, i) => <SkeletonRow key={i} />)}

        {/* Error state */}
        {!loading && error && (
          <div className="flex flex-col items-center justify-center h-full gap-3 p-8">
            <AlertTriangle size={28} style={{ color: '#EF4444' }} />
            <p className="text-sm font-bold" style={{ color: '#EF4444' }}>Failed to load alerts</p>
            <p className="text-xs terminal text-center" style={{ color: '#6B7280', maxWidth: 360 }}>{error}</p>
            <button onClick={fetchAlerts}
              className="mt-2 text-xs terminal px-4 py-2 rounded hover:brightness-125 transition-all"
              style={{ background: '#EF444418', color: '#EF4444', border: '1px solid #EF444433' }}>
              RETRY
            </button>
          </div>
        )}

        {/* Empty state */}
        {!loading && !error && filtered.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full gap-3">
            <ShieldOff size={32} style={{ color: '#1F2937' }} />
            <p className="text-sm font-bold" style={{ color: '#374151' }}>
              {alerts.length === 0 ? 'No alerts on record' : 'No alerts match current filters'}
            </p>
            <p className="text-xs terminal" style={{ color: '#4B5563' }}>
              {alerts.length === 0
                ? 'QUILL-TRIAGE has not generated any alerts yet.'
                : 'Try adjusting the severity or source filters.'}
            </p>
          </div>
        )}

        {/* Alert rows */}
        {!loading && !error && filtered.map(alert => {
          const s = SEVERITY_STYLES[alert.severity] || SEVERITY_STYLES['Low'];
          const isCritical = alert.severity === 'Critical';
          const isHigh = alert.severity === 'High';
          const sevClass = isCritical ? 'sev-critical' : isHigh ? 'sev-high' : alert.severity === 'Medium' ? 'sev-medium' : 'sev-low';
          return (
            <div key={alert.id}
              onClick={() => setSelectedAlert(selectedAlert?.id === alert.id ? null : alert)}
              className="grid items-center px-4 py-3 border-b cursor-pointer hover:brightness-125 transition-all animate-alert-bounce"
              style={{
                gridTemplateColumns: '100px 1fr 120px 80px 110px 130px 130px',
                borderColor: '#1F2937',
                background:  selectedAlert?.id === alert.id ? '#131d2e' : isCritical ? 'rgba(239,68,68,0.04)' : 'transparent',
                borderLeft:  isCritical ? '2px solid #EF4444' : isHigh ? '2px solid #E5A86244' : '2px solid transparent',
              }}>
              <span><SeverityBadge level={alert.severity} /></span>
              <span className={`h-title-sm ${sevClass}`}>{alert.title}</span>
              <span 
                className="h-body hover:underline cursor-pointer" 
                style={{ color: '#93C5FD' }}
                onClick={(e) => { e.stopPropagation(); setSelectedHost(alert.asset); }}
              >
                {alert.asset}
              </span>
              <span className="h-meta" style={{ color: '#6B7280', letterSpacing: '0.05em' }}>{alert.source}</span>
              <span className="h-meta">{alert.time}</span>
              <span className="h-meta px-2 py-0.5 rounded"
                style={{ background: '#D84C7F11', color: '#D84C7F99', border: '1px solid #D84C7F22' }}>
                {alert.mitre || '—'}
              </span>
              <div className="flex items-center gap-2">
                {alert.agent !== 'UNASSIGNED'
                  ? <span className="h-meta" style={{ color: '#3B6FE3' }}>{alert.agent}</span>
                  : <span className="h-meta" style={{ color: '#374151' }}>—</span>}
              </div>
            </div>
          );
        })}
      </div>

      {/* Expanded Alert Actions */}
      {selectedAlert && (
        <div className="border-t px-4 py-3 flex-shrink-0 flex flex-col gap-3 animate-slide-in-up"
          style={{ borderColor: `${(SEVERITY_STYLES[selectedAlert.severity] || SEVERITY_STYLES['Low']).border}55`, background: '#111827' }}>
          
          <div className="flex items-center gap-3">
            <div className="flex-1 text-xs" style={{ color: '#9CA3AF' }}>
              <span className="font-bold" style={{ color: '#E2E8F0' }}>{selectedAlert.id}</span>
              {' — '}{selectedAlert.description || selectedAlert.title}
              {selectedAlert.is_correlated && <span className="ml-2 text-[10px] terminal px-1.5 py-0.5 rounded" style={{ background: '#3B6FE322', color: '#3B6FE3', border: '1px solid #3B6FE344' }}>CORRELATED</span>}
            </div>
            <div className="flex gap-2">
              <button className="text-xs terminal px-3 py-1.5 rounded transition-all hover:brightness-125"
                style={{ background: '#3B6FE322', color: '#3B6FE3', border: '1px solid #3B6FE344' }}>
                Assign Agent
              </button>
              <button className="text-xs terminal px-3 py-1.5 rounded transition-all hover:brightness-125"
                style={{ background: '#D84C7F22', color: '#D84C7F', border: '1px solid #D84C7F44' }}>
                Promote to Investigation
              </button>
            </div>
          </div>

          {/* FTC (Fuzzy Threat Classification) Metrics Grid */}
          {selectedAlert.ftse_metrics && Object.keys(selectedAlert.ftse_metrics).length > 0 && (
            <div className="grid grid-cols-4 gap-2 border-t pt-3" style={{ borderColor: '#1F2937' }}>
              {Object.entries(selectedAlert.ftse_metrics).map(([key, val]) => (
                <div key={key} className="p-2 rounded" style={{ background: '#0B1117', border: '1px solid #1F2937' }}>
                  <p className="text-[9px] terminal uppercase opacity-40">{key.replace(/_/g, ' ')}</p>
                  <p className="text-xs font-bold terminal" style={{ color: val > 2 ? '#EF4444' : '#88C057' }}>
                    {typeof val === 'number' ? val.toFixed(3) : val}
                  </p>
                </div>
              ))}
              <div className="p-2 rounded text-[10px] terminal flex items-center justify-center opacity-50 italic">
                Vector: {selectedAlert.vector_id?.slice(0, 8)}
              </div>
            </div>
          )}

          {selectedAlert.semantic_detail && (
            <div className="p-2 rounded border" style={{ background: '#080d14', borderColor: '#1F2937' }}>
              <p className="text-[9px] terminal uppercase opacity-40 mb-1">Semantic Inference (GAGGLE-LOG-GUARDIAN)</p>
              <p className="text-xs italic" style={{ color: '#9CA3AF' }}>"{selectedAlert.semantic_detail}"</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
