import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  ClockIcon, ShieldAlert, Search, Filter, ChevronDown, ChevronRight,
  AlertTriangle, CheckCircle2, Loader2, RefreshCw, Archive,
  Activity, Cpu, Moon
} from 'lucide-react';
import { useAuth } from '../store/AuthContext';
import { useSOC } from '../store/SOCContext';

// ── Severity helpers ────────────────────────────────────────────────────────
const SEV = {
  CRITICAL: { color: '#EF4444', bg: 'rgba(239,68,68,0.1)',   label: 'CRITICAL' },
  HIGH:     { color: '#E5A862', bg: 'rgba(229,168,98,0.1)',  label: 'HIGH'     },
  WARNING:  { color: '#E5A862', bg: 'rgba(229,168,98,0.08)', label: 'WARNING'  },
  MEDIUM:   { color: '#3B6FE3', bg: 'rgba(59,111,227,0.1)',  label: 'MEDIUM'   },
  LOW:      { color: '#88C057', bg: 'rgba(136,192,87,0.1)',  label: 'LOW'      },
};
const sev = (s) => SEV[s?.toUpperCase?.()] || SEV.MEDIUM;

const STATUS_COLOR = {
  TRIAGE:      '#E5A862',
  SCOPING:     '#3B6FE3',
  ACTIVE:      '#D84C7F',
  INVESTIGATING:'#D84C7F',
  CONTAINMENT: '#E5A862',
  ERADICATION: '#88C057',
  CLOSED:      '#4B5563',
  RESOLVED:    '#4B5563',
};
const statusColor = (s) => STATUS_COLOR[s?.toUpperCase?.()] || '#6B7280';

const fmtDate = (iso) => {
  if (!iso) return '—';
  const d = new Date(iso);
  return d.toLocaleString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
    hour: '2-digit', minute: '2-digit', hour12: false,
  });
};

const relTime = (iso) => {
  if (!iso) return '';
  const diff = Date.now() - new Date(iso).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1)   return 'just now';
  if (m < 60)  return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24)  return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
};

// ── Case Card ───────────────────────────────────────────────────────────────
function CaseCard({ c, expanded, onToggle }) {
  const st = sev(c.severity);
  const steps = c.reasoning_steps || [];
  const actions = c.actions_taken || [];

  return (
    <div
      className="rounded-lg overflow-hidden transition-all"
      style={{ border: `1px solid ${expanded ? st.color + '55' : '#1F2937'}`, background: expanded ? st.bg : '#111827' }}>

      {/* Header row */}
      <button
        onClick={onToggle}
        className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-white/[0.02] transition-colors">
        {expanded
          ? <ChevronDown size={12} style={{ color: '#6B7280', flexShrink: 0 }} />
          : <ChevronRight size={12} style={{ color: '#6B7280', flexShrink: 0 }} />}

        {/* Severity pill */}
        <span className="text-[10px] terminal font-bold px-2 py-0.5 rounded flex-shrink-0"
          style={{ background: st.bg, color: st.color, border: `1px solid ${st.color}44` }}>
          {st.label}
        </span>

        {/* Case ID */}
        <span className="text-xs terminal font-bold flex-shrink-0" style={{ color: st.color }}>
          {c.case_id}
        </span>

        {/* Summary */}
        <span className="h-body text-sm truncate flex-1" style={{ color: '#CBD5E1' }}>
          {c.summary || c.alert_details?.description || 'Unnamed Case'}
        </span>

        {/* Status badge */}
        <span className="text-[10px] terminal px-2 py-0.5 rounded flex-shrink-0"
          style={{ background: `${statusColor(c.status)}18`, color: statusColor(c.status), border: `1px solid ${statusColor(c.status)}33` }}>
          {c.status || 'UNKNOWN'}
        </span>

        {/* Timestamp */}
        <span className="text-[10px] terminal flex-shrink-0" style={{ color: '#4B5563' }}>
          {relTime(c.created_at)}
        </span>
      </button>

      {/* Expanded detail */}
      {expanded && (
        <div className="px-5 pb-4 space-y-3 border-t" style={{ borderColor: '#1F2937' }}>
          {/* Key fields row */}
          <div className="flex flex-wrap gap-4 pt-3">
            {[
              { label: 'SOURCE IP',    value: c.source_ip          },
              { label: 'MITRE TTP',    value: c.mitre_ttp          },
              { label: 'NIST CONTROL', value: c.nist_control       },
              { label: 'CONFIDENCE',   value: c.confidence != null ? `${c.confidence}%` : '—' },
              { label: 'OPENED',       value: fmtDate(c.created_at)},
              { label: 'UPDATED',      value: fmtDate(c.updated_at)},
            ].map(({ label, value }) => value && (
              <div key={label}>
                <p className="text-[10px] terminal" style={{ color: '#4B5563' }}>{label}</p>
                <p className="text-xs terminal font-bold mt-0.5" style={{ color: '#9CA3AF' }}>{value}</p>
              </div>
            ))}
          </div>

          {/* Hypothesis */}
          {c.hypothesis && (
            <div className="rounded p-3" style={{ background: '#0B1117', border: '1px solid #1F2937' }}>
              <p className="text-[10px] terminal mb-1" style={{ color: '#4B5563' }}>HYPOTHESIS</p>
              <p className="text-xs" style={{ color: '#9CA3AF' }}>{c.hypothesis}</p>
            </div>
          )}

          {/* Reasoning steps */}
          {steps.length > 0 && (
            <div>
              <p className="text-[10px] terminal mb-2" style={{ color: '#4B5563' }}>
                REASONING CHAIN ({steps.length} steps)
              </p>
              <div className="space-y-1 max-h-36 overflow-y-auto">
                {steps.map((step, i) => (
                  <div key={i} className="flex gap-2 text-[11px] terminal" style={{ color: '#6B7280' }}>
                    <span style={{ color: '#374151' }}>{String(i + 1).padStart(2, '0')}</span>
                    <span>{step}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Actions taken */}
          {actions.length > 0 && (
            <div>
              <p className="text-[10px] terminal mb-2" style={{ color: '#4B5563' }}>
                ACTIONS ({actions.length})
              </p>
              {actions.map((a, i) => (
                <div key={i} className="text-[11px] terminal flex gap-2" style={{ color: '#9CA3AF' }}>
                  <CheckCircle2 size={10} style={{ color: '#88C057', flexShrink: 0, marginTop: 1 }} />
                  <span>{typeof a === 'string' ? a : JSON.stringify(a)}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Dormant Entity Alert Row ─────────────────────────────────────────────────
function DormantRow({ alert }) {
  const st = sev(alert.severity);
  return (
    <div className="flex items-start gap-3 px-4 py-3 rounded-lg"
         style={{ background: '#0B1117', border: `1px solid ${st.color}33` }}>
      <Moon size={13} style={{ color: st.color, flexShrink: 0, marginTop: 1 }} />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-0.5">
          <span className="text-[10px] terminal font-bold" style={{ color: st.color }}>
            {alert.severity}
          </span>
          <span className="text-[10px] terminal" style={{ color: '#4B5563' }}>
            {relTime(alert.timestamp)}
          </span>
        </div>
        <p className="text-xs" style={{ color: '#CBD5E1' }}>{alert.description}</p>
        {alert.mitre_ttp && (
          <p className="text-[10px] terminal mt-1" style={{ color: '#4B5563' }}>
            {alert.mitre_ttp} · NIST {alert.nist_control}
          </p>
        )}
      </div>
    </div>
  );
}

// ── Main View ───────────────────────────────────────────────────────────────
export default function CaseHistoryView() {
  const { authenticatedFetch } = useAuth();
  const { alerts: contextAlerts, investigations: contextCases } = useSOC();

  const [cases, setCases]         = useState([]);
  const [loading, setLoading]     = useState(true);
  const [search, setSearch]       = useState('');
  const [sevFilter, setSevFilter] = useState('ALL');
  const [expandedId, setExpandedId] = useState(null);
  const [activeTab, setActiveTab] = useState('cases'); // 'cases' | 'dormant'

  const fetchCases = useCallback(async () => {
    setLoading(true);
    try {
      const res = await authenticatedFetch('http://localhost:8000/cases');
      if (res.ok) {
        const data = await res.json();
        setCases(data);
      }
    } catch (err) {
      console.error('[CaseHistory] Failed to fetch cases:', err);
    } finally {
      setLoading(false);
    }
  }, [authenticatedFetch]);

  useEffect(() => {
    fetchCases();
  }, [fetchCases]);

  // Prefer live-fetched cases; fall back to SOCContext investigations if backend has none
  const allCases = cases.length > 0 ? cases : contextCases;

  // Historian dormant-entity alerts — filter from the live alert feed
  const dormantAlerts = useMemo(() =>
    (contextAlerts || []).filter(a =>
      a.rule_id === 'HISTORIAN_DORMANT_WAKE' ||
      a.rule_name?.toLowerCase().includes('dormant') ||
      a.rule_name?.toLowerCase().includes('historian')
    ), [contextAlerts]);

  // Filter + search
  const filteredCases = useMemo(() => {
    let list = [...allCases];
    if (sevFilter !== 'ALL') {
      list = list.filter(c => c.severity?.toUpperCase() === sevFilter);
    }
    if (search.trim()) {
      const q = search.toLowerCase();
      list = list.filter(c =>
        c.case_id?.toLowerCase().includes(q) ||
        c.summary?.toLowerCase().includes(q) ||
        c.source_ip?.toLowerCase().includes(q) ||
        c.mitre_ttp?.toLowerCase().includes(q)
      );
    }
    return list;
  }, [allCases, sevFilter, search]);

  // Stats
  const critical = allCases.filter(c => c.severity?.toUpperCase() === 'CRITICAL').length;
  const open     = allCases.filter(c => !['CLOSED','RESOLVED'].includes(c.status?.toUpperCase())).length;

  const SEV_FILTERS = ['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'];

  return (
    <div className="flex flex-col h-full" style={{ background: '#0B1117' }}>

      {/* ── Header ── */}
      <div className="flex items-center justify-between px-5 py-3 border-b flex-shrink-0"
           style={{ borderColor: '#1F2937', background: '#0d1117' }}>
        <div className="flex items-center gap-3">
          <Archive size={14} style={{ color: '#D84C7F' }} />
          <span className="text-xs font-bold tracking-widest" style={{ color: '#E2E8F0' }}>
            CASE HISTORY &amp; TEMPORAL INTELLIGENCE
          </span>
          <span className="text-[10px] terminal px-2 py-0.5 rounded-full"
            style={{ background: '#D84C7F18', color: '#D84C7F', border: '1px solid #D84C7F33' }}>
            SENTINEL-HISTORIAN
          </span>
        </div>
        <button
          onClick={fetchCases}
          className={`p-1.5 rounded hover:bg-white/5 transition-colors ${loading ? 'animate-spin' : ''}`}>
          <RefreshCw size={13} style={{ color: loading ? '#D84C7F' : '#6B7280' }} />
        </button>
      </div>

      {/* ── KPI Strip ── */}
      <div className="grid grid-cols-4 border-b flex-shrink-0"
           style={{ borderColor: '#1F2937', background: '#080c12' }}>
        {[
          { label: 'TOTAL CASES',     value: allCases.length,  color: '#E2E8F0', icon: Archive },
          { label: 'OPEN',            value: open,             color: '#E5A862', icon: Activity },
          { label: 'CRITICAL',        value: critical,         color: '#EF4444', icon: ShieldAlert },
          { label: 'DORMANT ALERTS',  value: dormantAlerts.length, color: '#D84C7F', icon: Moon },
        ].map(({ label, value, color, icon: Icon }) => (
          <div key={label} className="flex items-center gap-3 px-5 py-3 border-r last:border-0"
               style={{ borderColor: '#1F2937' }}>
            <Icon size={14} style={{ color, opacity: 0.7, flexShrink: 0 }} />
            <div>
              <p className="h-stat text-xl font-bold" style={{ color }}>{value}</p>
              <p className="h-meta" style={{ color: '#4B5563' }}>{label}</p>
            </div>
          </div>
        ))}
      </div>

      {/* ── Tab bar ── */}
      <div className="flex border-b flex-shrink-0" style={{ borderColor: '#1F2937', background: '#0d1117' }}>
        {[
          { id: 'cases',   label: 'CASE ARCHIVE',    count: allCases.length, color: '#D84C7F' },
          { id: 'dormant', label: 'DORMANT ENTITIES', count: dormantAlerts.length, color: '#E5A862' },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className="flex items-center gap-2 px-5 py-2.5 text-xs terminal transition-colors border-b-2"
            style={{
              borderColor: activeTab === tab.id ? tab.color : 'transparent',
              color: activeTab === tab.id ? tab.color : '#4B5563',
            }}>
            {tab.label}
            <span className="px-1.5 py-0.5 rounded-full text-[10px]"
              style={{
                background: activeTab === tab.id ? `${tab.color}22` : '#1F2937',
                color: activeTab === tab.id ? tab.color : '#4B5563',
              }}>
              {tab.count}
            </span>
          </button>
        ))}
      </div>

      {/* ── Toolbar (cases tab only) ── */}
      {activeTab === 'cases' && (
        <div className="flex items-center gap-3 px-4 py-2 border-b flex-shrink-0"
             style={{ borderColor: '#1F2937', background: '#080c12' }}>
          {/* Search */}
          <div className="flex items-center gap-2 flex-1 max-w-xs px-3 py-1.5 rounded-lg"
               style={{ background: '#111827', border: '1px solid #1F2937' }}>
            <Search size={11} style={{ color: '#4B5563' }} />
            <input
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Search case ID, IP, TTP..."
              className="bg-transparent text-xs terminal outline-none flex-1"
              style={{ color: '#CBD5E1' }}
            />
          </div>
          {/* Severity filters */}
          <div className="flex items-center gap-1.5">
            <Filter size={11} style={{ color: '#4B5563' }} />
            {SEV_FILTERS.map(f => (
              <button key={f}
                onClick={() => setSevFilter(f)}
                className="text-[10px] terminal px-2.5 py-1 rounded-full transition-all"
                style={{
                  background: sevFilter === f ? (SEV[f]?.bg || '#1F293788') : 'transparent',
                  color:      sevFilter === f ? (SEV[f]?.color || '#E2E8F0') : '#4B5563',
                  border:     `1px solid ${sevFilter === f ? (SEV[f]?.color || '#E2E8F0') + '44' : '#1F2937'}`,
                }}>
                {f}
              </button>
            ))}
          </div>
          <span className="ml-auto text-[10px] terminal" style={{ color: '#4B5563' }}>
            {filteredCases.length} result{filteredCases.length !== 1 ? 's' : ''}
          </span>
        </div>
      )}

      {/* ── Body ── */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-2">

        {/* Cases tab */}
        {activeTab === 'cases' && (
          <>
            {loading && allCases.length === 0 && (
              <div className="flex items-center justify-center h-48 gap-3">
                <Loader2 className="animate-spin" size={20} style={{ color: '#D84C7F' }} />
                <p className="text-xs terminal" style={{ color: '#D84C7F' }}>
                  Retrieving case archive from SENTINEL-HISTORIAN…
                </p>
              </div>
            )}

            {!loading && filteredCases.length === 0 && (
              <div className="flex flex-col items-center justify-center h-48 gap-3">
                <Archive size={28} style={{ color: '#1F2937' }} />
                <p className="text-xs terminal" style={{ color: '#4B5563' }}>
                  {search || sevFilter !== 'ALL' ? 'No cases match your filters.' : 'No archived cases found.'}
                </p>
              </div>
            )}

            {/* Timeline */}
            <div className="relative">
              {/* Vertical line */}
              {filteredCases.length > 0 && (
                <div className="absolute left-[11px] top-4 bottom-4 w-px"
                     style={{ background: 'linear-gradient(to bottom, #D84C7F44, #1F2937)' }} />
              )}
              <div className="space-y-2 pl-6">
                {filteredCases.map((c) => (
                  <div key={c.case_id} className="relative">
                    {/* Timeline dot */}
                    <div className="absolute -left-6 top-3.5 w-2 h-2 rounded-full border"
                         style={{
                           background: sev(c.severity).color,
                           borderColor: sev(c.severity).color,
                           boxShadow: `0 0 6px ${sev(c.severity).color}66`,
                         }} />
                    <CaseCard
                      c={c}
                      expanded={expandedId === c.case_id}
                      onToggle={() => setExpandedId(p => p === c.case_id ? null : c.case_id)}
                    />
                  </div>
                ))}
              </div>
            </div>
          </>
        )}

        {/* Dormant entities tab */}
        {activeTab === 'dormant' && (
          <>
            {dormantAlerts.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-48 gap-4">
                <div className="w-14 h-14 rounded-2xl flex items-center justify-center"
                     style={{ background: '#111827', border: '1px solid #1F2937' }}>
                  <Moon size={24} style={{ color: '#E5A86233' }} />
                </div>
                <div className="text-center">
                  <p className="h-title" style={{ color: '#6B7280' }}>No Dormant Entities Detected</p>
                  <p className="h-meta mt-1" style={{ color: '#374151' }}>
                    SENTINEL-HISTORIAN is monitoring all known entities.<br />
                    Alerts fire when an entity reappears after {'>'}30 days of silence.
                  </p>
                </div>
              </div>
            ) : (
              <div className="space-y-2">
                <p className="text-[10px] terminal px-1 pb-1" style={{ color: '#4B5563' }}>
                  HISTORIAN_DORMANT_WAKE EVENTS — THRESHOLD: 30 DAYS
                </p>
                {dormantAlerts.map((a, i) => (
                  <DormantRow key={a.rule_id + i} alert={a} />
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
