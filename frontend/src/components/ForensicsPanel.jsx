import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  FlaskConical, RefreshCw, ShieldAlert, Hash, Database,
  Layers, AlertTriangle, CheckCircle2, Loader2, ChevronRight,
  ChevronDown, Server, Clock, FileSearch, Link2, Archive
} from 'lucide-react';
import { useAuth } from '../store/AuthContext';

// ── Helpers ──────────────────────────────────────────────────────────────────
const ARTIFACT_META = {
  MEMORY:   { color: '#EF4444', bg: 'rgba(239,68,68,0.08)',   icon: '🧠', label: 'Memory Dump'    },
  REGISTRY: { color: '#E5A862', bg: 'rgba(229,168,98,0.08)',  icon: '🗝', label: 'Registry Hive'  },
  PCAP:     { color: '#3B6FE3', bg: 'rgba(59,111,227,0.08)',  icon: '📡', label: 'Network Capture' },
  LOGS:     { color: '#88C057', bg: 'rgba(136,192,87,0.08)',  icon: '📄', label: 'Event Logs'     },
};
const artifactMeta = (t) => ARTIFACT_META[t?.toUpperCase?.()] || ARTIFACT_META.LOGS;

const RISK_COLOR = { CRITICAL: '#EF4444', HIGH: '#E5A862', MEDIUM: '#3B6FE3', LOW: '#88C057' };
const riskColor  = (r) => RISK_COLOR[r?.toUpperCase?.()] || '#6B7280';

const relTime = (iso) => {
  if (!iso) return '—';
  const diff = Date.now() - new Date(iso).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1)  return 'just now';
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
};

const fmtDate = (iso) => {
  if (!iso) return '—';
  return new Date(iso).toLocaleString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
    hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false,
  });
};

// ── Mock evidence (fallback when backend has no data) ─────────────────────────
const MOCK_EVIDENCE = [
  {
    evidence_id:      'EVD_20260316_195529_862',
    case_id:          'INC-HARDEN-TEST-001',
    target_ip:        '192.168.1.105',
    artifact_type:    'MEMORY',
    collected_at:     new Date(Date.now() - 3600000 * 3).toISOString(),
    findings_summary: 'Potential threat headers found: SHELLCODE_STUB, PE_HEADER_IN_MEM.',
    threat_score:     90,
    patterns: [
      { header: 'SHELLCODE_STUB',   offset: '0x00000450', risk: 'CRITICAL' },
      { header: 'PE_HEADER_IN_MEM', offset: '0x00400000', risk: 'HIGH'     },
    ],
    integrity: { algorithm: 'SHA-256', hash: 'a3f9...efbb', seal: 'ALIGNED_WITH_NIST_3.14.3' },
    storage:   { storage_mode: 'PAGED', page_count: 3, total_size_bytes: 1420 },
    data: {
      pid: 9912, process: 'svchost.exe',
      indicators: [
        { type: 'reflective_load',    address: '0x00401000', size: '1.2MB' },
        { type: 'suspicious_string',  value: 'sekurlsa::logonpasswords' },
        { type: 'beacon_pattern',     interval: '60s' },
      ],
    },
  },
  {
    evidence_id:      'EVD_20260316_195736_441',
    case_id:          'INC-HARDEN-REFINE-01',
    target_ip:        '10.0.0.50',
    artifact_type:    'REGISTRY',
    collected_at:     new Date(Date.now() - 3600000 * 6).toISOString(),
    findings_summary: 'Suspicious Run key pointing to Temp directory executable.',
    threat_score:     75,
    patterns: [
      { header: 'SUSPICIOUS_RUNKEY', offset: 'HKLM\\Run', risk: 'HIGH' },
    ],
    integrity: { algorithm: 'SHA-256', hash: 'c8d1...7f3a', seal: 'ALIGNED_WITH_NIST_3.14.3' },
    storage:   { storage_mode: 'SINGLE_PAGE', page_count: 1, total_size_bytes: 340 },
    data: {
      'HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run': {
        'RCA_Update': 'C:\\Windows\\Temp\\svchost_update.exe',
        'OneDrive':   'C:\\Users\\admin\\AppData\\Local\\Microsoft\\OneDrive\\OneDrive.exe',
      },
      'HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\RunOnce': {
        'InstallUpdate': 'powershell.exe -ExecutionPolicy Bypass -File C:\\Temp\\s.ps1',
      },
    },
  },
  {
    evidence_id:      'EVD_20260316_200011_123',
    case_id:          'INC-HARDEN-TEST-001',
    target_ip:        '192.168.1.105',
    artifact_type:    'PCAP',
    collected_at:     new Date(Date.now() - 3600000 * 7).toISOString(),
    findings_summary: 'Standard forensic collection.',
    threat_score:     0,
    patterns: [],
    integrity: { algorithm: 'SHA-256', hash: 'b4e2...c9d8', seal: 'ALIGNED_WITH_NIST_3.14.3' },
    storage:   { storage_mode: 'SINGLE_PAGE', page_count: 1, total_size_bytes: 580 },
    data: [
      { timestamp: '10:01:22', proto: 'TCP', src: '192.168.1.105', dst: '203.0.113.45', len: 1024, flag: 'PSH,ACK' },
      { timestamp: '10:02:22', proto: 'TCP', src: '192.168.1.105', dst: '203.0.113.45', len: 128,  flag: 'PSH,ACK' },
      { timestamp: '10:03:22', proto: 'TCP', src: '192.168.1.105', dst: '203.0.113.45', len: 512,  flag: 'PSH,ACK' },
    ],
  },
];

const MOCK_COC = {
  document_title: 'Enterprise Chain of Custody Log',
  compliance: 'NIST 800-171 Rev 3 (3.3.1, 3.6.1)',
  events: [
    { timestamp: MOCK_EVIDENCE[0].collected_at, event: 'COLLECTION', evidence_id: MOCK_EVIDENCE[0].evidence_id, case_id: 'INC-HARDEN-TEST-001', target: '192.168.1.105', actor: 'FORENSICS-01', status: 'SECURED' },
    { timestamp: MOCK_EVIDENCE[1].collected_at, event: 'COLLECTION', evidence_id: MOCK_EVIDENCE[1].evidence_id, case_id: 'INC-HARDEN-REFINE-01', target: '10.0.0.50', actor: 'FORENSICS-01', status: 'SECURED' },
    { timestamp: MOCK_EVIDENCE[2].collected_at, event: 'COLLECTION', evidence_id: MOCK_EVIDENCE[2].evidence_id, case_id: 'INC-HARDEN-TEST-001', target: '192.168.1.105', actor: 'FORENSICS-01', status: 'SECURED' },
  ],
};

// ── Pattern badge ─────────────────────────────────────────────────────────────
function PatternBadge({ p }) {
  return (
    <div className="flex items-center gap-2 px-3 py-2 rounded-lg"
         style={{ background: `${riskColor(p.risk)}0E`, border: `1px solid ${riskColor(p.risk)}33` }}>
      <ShieldAlert size={11} style={{ color: riskColor(p.risk), flexShrink: 0 }} />
      <div className="min-w-0">
        <p className="text-[10px] terminal font-bold" style={{ color: riskColor(p.risk) }}>{p.risk} — {p.header}</p>
        <p className="text-[10px] terminal" style={{ color: '#4B5563' }}>Offset: {p.offset}</p>
      </div>
    </div>
  );
}

// ── Data preview ─────────────────────────────────────────────────────────────
function DataPreview({ data, artifactType }) {
  const str = useMemo(() => {
    try { return JSON.stringify(data, null, 2); }
    catch { return String(data); }
  }, [data]);

  const lines = str.split('\n');
  return (
    <div className="rounded-lg overflow-hidden" style={{ border: '1px solid #1F2937', background: '#080c12' }}>
      <div className="px-3 py-2 border-b flex items-center gap-2" style={{ borderColor: '#1F2937' }}>
        <Database size={11} style={{ color: '#4B5563' }} />
        <span className="text-[10px] terminal" style={{ color: '#4B5563' }}>RAW ARTIFACT DATA</span>
        <span className="ml-auto text-[10px] terminal" style={{ color: '#374151' }}>{lines.length} lines</span>
      </div>
      <div className="overflow-auto max-h-48 p-3">
        <pre className="text-[10px] leading-5" style={{ fontFamily: 'JetBrains Mono, monospace', color: '#9CA3AF' }}>
          {lines.map((line, i) => {
            let color = '#9CA3AF';
            if (/"type"|"process"|"pid"|"header"/.test(line)) color = '#93C5FD';
            if (/"CRITICAL"|"HIGH"|"suspicious_string"/.test(line)) color = '#FCA5A5';
            if (/0x[0-9A-Fa-f]+/.test(line)) color = '#FCD34D';
            if (/^\s*"[A-Z_]+":/.test(line)) color = '#DDD6FE';
            return (
              <div key={i} className="flex gap-3">
                <span className="select-none w-6 text-right flex-shrink-0" style={{ color: '#374151' }}>{i + 1}</span>
                <span style={{ color }}>{line || ' '}</span>
              </div>
            );
          })}
        </pre>
      </div>
    </div>
  );
}

// ── Evidence card ─────────────────────────────────────────────────────────────
function EvidenceCard({ ev, expanded, onToggle }) {
  const am = artifactMeta(ev.artifact_type);
  const hasThreats = ev.patterns?.length > 0;

  return (
    <div className="rounded-lg overflow-hidden transition-all"
         style={{
           border: `1px solid ${expanded ? (hasThreats ? '#EF444455' : '#1F2937') : '#1F2937'}`,
           background: expanded ? (hasThreats ? 'rgba(239,68,68,0.04)' : '#111827') : '#111827',
         }}>
      {/* Card header */}
      <button onClick={onToggle}
        className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-white/[0.02] transition-colors">
        {expanded
          ? <ChevronDown size={11} style={{ color: '#6B7280', flexShrink: 0 }} />
          : <ChevronRight size={11} style={{ color: '#6B7280', flexShrink: 0 }} />}

        {/* Type pill */}
        <span className="text-[10px] terminal px-2 py-0.5 rounded flex-shrink-0 flex items-center gap-1"
              style={{ background: am.bg, color: am.color, border: `1px solid ${am.color}33` }}>
          {am.icon} {am.label}
        </span>

        {/* Evidence ID */}
        <span className="text-xs terminal font-bold flex-shrink-0 truncate max-w-[160px]"
              style={{ color: am.color }}>
          {ev.evidence_id}
        </span>

        {/* Summary */}
        <span className="text-xs truncate flex-1" style={{ color: '#9CA3AF' }}>
          {ev.findings_summary}
        </span>

        {/* Threat score */}
        {ev.threat_score > 0 && (
          <span className="text-[10px] terminal font-bold px-2 py-0.5 rounded flex-shrink-0"
                style={{ background: '#EF444418', color: '#EF4444', border: '1px solid #EF444433' }}>
            ⚠ THREAT {ev.threat_score}
          </span>
        )}

        {/* Timestamp */}
        <span className="text-[10px] terminal flex-shrink-0" style={{ color: '#374151' }}>
          {relTime(ev.collected_at)}
        </span>
      </button>

      {/* Expanded detail */}
      {expanded && (
        <div className="px-5 pb-4 space-y-3 border-t" style={{ borderColor: '#1F2937' }}>
          {/* Meta row */}
          <div className="flex flex-wrap gap-5 pt-3">
            {[
              { label: 'CASE ID',    value: ev.case_id,           icon: Archive },
              { label: 'TARGET IP',  value: ev.target_ip,         icon: Server  },
              { label: 'COLLECTED',  value: fmtDate(ev.collected_at), icon: Clock },
              { label: 'STORAGE',    value: ev.storage?.storage_mode, icon: Database },
              { label: 'PAGES',      value: ev.storage?.page_count != null ? `${ev.storage.page_count} page${ev.storage.page_count !== 1 ? 's' : ''}` : null, icon: Layers },
              { label: 'SIZE',       value: ev.storage?.total_size_bytes != null ? `${ev.storage.total_size_bytes} bytes` : null, icon: Layers },
            ].filter(f => f.value).map(({ label, value, icon: Icon }) => (
              <div key={label}>
                <div className="flex items-center gap-1 mb-0.5">
                  <Icon size={9} style={{ color: '#374151' }} />
                  <p className="text-[10px] terminal" style={{ color: '#4B5563' }}>{label}</p>
                </div>
                <p className="text-xs terminal font-bold" style={{ color: '#9CA3AF' }}>{value}</p>
              </div>
            ))}
          </div>

          {/* IQ: Threat patterns */}
          {ev.patterns?.length > 0 && (
            <div>
              <p className="text-[10px] terminal mb-2 flex items-center gap-1.5" style={{ color: '#4B5563' }}>
                <ShieldAlert size={10} style={{ color: '#EF4444' }} />
                IQ PATTERN ANALYSIS — {ev.patterns.length} threat indicator{ev.patterns.length !== 1 ? 's' : ''} detected
              </p>
              <div className="grid grid-cols-2 gap-2">
                {ev.patterns.map((p, i) => <PatternBadge key={i} p={p} />)}
              </div>
            </div>
          )}

          {/* EQ: Integrity seal */}
          {ev.integrity?.hash && (
            <div className="flex items-center gap-3 px-3 py-2 rounded-lg"
                 style={{ background: '#88C05709', border: '1px solid #88C05733' }}>
              <CheckCircle2 size={12} style={{ color: '#88C057', flexShrink: 0 }} />
              <div className="min-w-0 flex-1">
                <p className="text-[10px] terminal" style={{ color: '#4B5563' }}>
                  EQ INTEGRITY SEAL — {ev.integrity.algorithm} · {ev.integrity.seal}
                </p>
                <p className="text-[10px] terminal font-bold mt-0.5 truncate" style={{ color: '#88C05799' }}>
                  {ev.integrity.hash}
                </p>
              </div>
              <Hash size={11} style={{ color: '#88C05766' }} />
            </div>
          )}

          {/* Data preview */}
          {ev.data && <DataPreview data={ev.data} artifactType={ev.artifact_type} />}
        </div>
      )}
    </div>
  );
}

// ── CoC event row ─────────────────────────────────────────────────────────────
function CoCRow({ event }) {
  return (
    <div className="flex items-center gap-3 px-4 py-2.5 border-b last:border-0"
         style={{ borderColor: '#1F2937' }}>
      <div className="w-1.5 h-1.5 rounded-full flex-shrink-0"
           style={{ background: '#88C057', boxShadow: '0 0 4px rgba(136,192,87,0.6)' }} />
      <span className="text-[10px] terminal font-bold flex-shrink-0"
            style={{ color: '#88C057', minWidth: 80 }}>{event.event}</span>
      <span className="text-[10px] terminal flex-shrink-0" style={{ color: '#3B6FE3', minWidth: 160 }}>
        {event.evidence_id}
      </span>
      <span className="text-[10px] terminal flex-shrink-0" style={{ color: '#6B7280', minWidth: 140 }}>
        {event.case_id}
      </span>
      <span className="text-[10px] terminal flex-shrink-0" style={{ color: '#4B5563', minWidth: 120 }}>
        {event.target}
      </span>
      <span className="text-[10px] terminal" style={{ color: '#4B5563' }}>
        {event.actor}
      </span>
      <span className="ml-auto text-[10px] terminal" style={{ color: '#374151' }}>
        {relTime(event.timestamp)}
      </span>
    </div>
  );
}

// ── Main view ─────────────────────────────────────────────────────────────────
export default function ForensicsPanel() {
  const { authenticatedFetch } = useAuth();

  const [evidence,  setEvidence]  = useState([]);
  const [coc,       setCoc]       = useState(null);
  const [loading,   setLoading]   = useState(true);
  const [isMock,    setIsMock]    = useState(false);
  const [activeTab, setActiveTab] = useState('evidence');  // 'evidence' | 'coc'
  const [expandedId, setExpandedId] = useState(null);
  const [typeFilter, setTypeFilter] = useState('ALL');

  const fetchAll = useCallback(async () => {
    setLoading(true);
    try {
      const [evRes, cocRes] = await Promise.all([
        authenticatedFetch('http://localhost:8000/api/v1/forensics'),
        authenticatedFetch('http://localhost:8000/api/v1/forensics/chain-of-custody'),
      ]);

      let gotLive = false;
      if (evRes.ok) {
        const data = await evRes.json();
        if (data.length > 0) { setEvidence(data); gotLive = true; }
      }
      if (cocRes.ok) {
        const data = await cocRes.json();
        setCoc(data);
      }
      if (!gotLive) throw new Error('empty');
      setIsMock(false);
    } catch {
      setEvidence(MOCK_EVIDENCE);
      setCoc(MOCK_COC);
      setIsMock(true);
    } finally {
      setLoading(false);
    }
  }, [authenticatedFetch]);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const filtered = useMemo(() =>
    typeFilter === 'ALL' ? evidence : evidence.filter(e => e.artifact_type === typeFilter),
    [evidence, typeFilter]
  );

  // KPIs
  const threatCount = evidence.filter(e => e.threat_score > 0).length;
  const caseSet     = new Set(evidence.map(e => e.case_id));
  const cocCount    = coc?.events?.length || 0;

  const TYPES = ['ALL', 'MEMORY', 'REGISTRY', 'PCAP', 'LOGS'];

  return (
    <div className="flex flex-col h-full" style={{ background: '#0B1117' }}>

      {/* ── Header ── */}
      <div className="flex items-center justify-between px-5 py-3 border-b flex-shrink-0"
           style={{ borderColor: '#1F2937', background: '#0d1117' }}>
        <div className="flex items-center gap-3">
          <FlaskConical size={14} style={{ color: '#D84C7F' }} />
          <span className="text-xs font-bold tracking-widest" style={{ color: '#E2E8F0' }}>
            FORENSICS EVIDENCE INSPECTOR
          </span>
          <span className="text-[10px] terminal px-2 py-0.5 rounded-full"
                style={{ background: '#D84C7F18', color: '#D84C7F', border: '1px solid #D84C7F33' }}>
            SENTINEL-FORENSICS
          </span>
          {isMock && (
            <span className="text-[10px] terminal px-2 py-0.5 rounded-full"
                  style={{ background: '#E5A86218', color: '#E5A862', border: '1px solid #E5A86244' }}>
              DEMO DATA
            </span>
          )}
        </div>
        <button
          onClick={fetchAll}
          className={`p-1.5 rounded hover:bg-white/5 transition-colors ${loading ? 'animate-spin' : ''}`}>
          <RefreshCw size={13} style={{ color: loading ? '#D84C7F' : '#6B7280' }} />
        </button>
      </div>

      {/* ── KPI Strip ── */}
      <div className="grid grid-cols-4 border-b flex-shrink-0"
           style={{ borderColor: '#1F2937', background: '#080c12' }}>
        {[
          { label: 'ARTIFACTS COLLECTED', value: evidence.length,    color: '#E2E8F0', icon: FileSearch },
          { label: 'ACTIVE CASES',        value: caseSet.size,       color: '#3B6FE3', icon: Archive    },
          { label: 'THREAT INDICATORS',   value: threatCount,        color: '#EF4444', icon: ShieldAlert },
          { label: 'CHAIN OF CUSTODY',    value: `${cocCount} events`,color: '#88C057', icon: Link2      },
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

      {/* ── Tabs ── */}
      <div className="flex border-b flex-shrink-0" style={{ borderColor: '#1F2937', background: '#0d1117' }}>
        {[
          { id: 'evidence', label: 'EVIDENCE VAULT',      count: evidence.length,  color: '#D84C7F' },
          { id: 'coc',      label: 'CHAIN OF CUSTODY',    count: cocCount,         color: '#88C057' },
        ].map(tab => (
          <button key={tab.id} onClick={() => setActiveTab(tab.id)}
            className="flex items-center gap-2 px-5 py-2.5 text-xs terminal transition-colors border-b-2"
            style={{
              borderColor: activeTab === tab.id ? tab.color : 'transparent',
              color:       activeTab === tab.id ? tab.color : '#4B5563',
            }}>
            {tab.label}
            <span className="px-1.5 py-0.5 rounded-full text-[10px]"
                  style={{
                    background: activeTab === tab.id ? `${tab.color}22` : '#1F2937',
                    color:      activeTab === tab.id ? tab.color : '#4B5563',
                  }}>
              {tab.count}
            </span>
          </button>
        ))}
      </div>

      {/* ── Body ── */}
      {loading && evidence.length === 0 ? (
        <div className="flex-1 flex items-center justify-center gap-3">
          <Loader2 className="animate-spin" size={20} style={{ color: '#D84C7F' }} />
          <p className="text-xs terminal" style={{ color: '#D84C7F' }}>
            Retrieving forensic artifacts from SENTINEL-FORENSICS…
          </p>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto">

          {/* ── EVIDENCE tab ── */}
          {activeTab === 'evidence' && (
            <div>
              {/* Type filter bar */}
              <div className="flex items-center gap-2 px-4 py-2 border-b sticky top-0 z-10"
                   style={{ borderColor: '#1F2937', background: '#080c12' }}>
                {TYPES.map(t => {
                  const m = t === 'ALL' ? null : artifactMeta(t);
                  return (
                    <button key={t} onClick={() => setTypeFilter(t)}
                      className="text-[10px] terminal px-2.5 py-1 rounded-full transition-all"
                      style={{
                        background: typeFilter === t ? (m ? m.bg : '#1F293788') : 'transparent',
                        color:      typeFilter === t ? (m ? m.color : '#E2E8F0') : '#4B5563',
                        border: `1px solid ${typeFilter === t ? (m ? m.color + '44' : '#374151') : '#1F2937'}`,
                      }}>
                      {t === 'ALL' ? 'All' : `${m.icon} ${m.label}`}
                    </button>
                  );
                })}
                <span className="ml-auto text-[10px] terminal" style={{ color: '#374151' }}>
                  {filtered.length} artifact{filtered.length !== 1 ? 's' : ''}
                </span>
              </div>

              {/* Evidence list */}
              <div className="p-4 space-y-2">
                {filtered.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-20 gap-3">
                    <FlaskConical size={28} style={{ color: '#1F2937' }} />
                    <p className="text-xs terminal" style={{ color: '#4B5563' }}>
                      No forensic artifacts found for this filter.
                    </p>
                  </div>
                ) : filtered.map(ev => (
                  <EvidenceCard
                    key={ev.evidence_id}
                    ev={ev}
                    expanded={expandedId === ev.evidence_id}
                    onToggle={() => setExpandedId(p => p === ev.evidence_id ? null : ev.evidence_id)}
                  />
                ))}
              </div>
            </div>
          )}

          {/* ── CHAIN OF CUSTODY tab ── */}
          {activeTab === 'coc' && (
            <div>
              {/* CoC header */}
              {coc && (
                <div className="px-5 py-3 border-b" style={{ borderColor: '#1F2937', background: '#080c12' }}>
                  <p className="text-xs terminal font-bold" style={{ color: '#E2E8F0' }}>
                    {coc.document_title}
                  </p>
                  <p className="text-[10px] terminal mt-0.5" style={{ color: '#4B5563' }}>
                    {coc.compliance}
                  </p>
                </div>
              )}
              {/* Column headers */}
              <div className="flex items-center gap-3 px-4 py-2 border-b"
                   style={{ borderColor: '#1F2937', background: '#0d1117' }}>
                {['EVENT', 'EVIDENCE ID', 'CASE ID', 'TARGET', 'ACTOR', ''].map((h, i) => (
                  <span key={i} className="text-[10px] terminal"
                        style={{ color: '#374151', minWidth: i === 0 ? 80 : i === 1 ? 160 : i === 2 ? 140 : i === 3 ? 120 : i === 4 ? 'auto' : 0 }}>
                    {h}
                  </span>
                ))}
              </div>
              {/* CoC events */}
              <div>
                {coc?.events?.length ? (
                  [...coc.events].reverse().map((ev, i) => (
                    <CoCRow key={i} event={ev} />
                  ))
                ) : (
                  <div className="flex flex-col items-center justify-center py-20 gap-3">
                    <Link2 size={28} style={{ color: '#1F2937' }} />
                    <p className="text-xs terminal" style={{ color: '#4B5563' }}>
                      No chain of custody events logged yet.
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
