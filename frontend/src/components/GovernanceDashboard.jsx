import React, { useState } from 'react';
import { Shield, BookOpen, FileText, ChevronDown, ChevronRight, CheckCircle, XCircle, AlertCircle } from 'lucide-react';

// ── Mock Data ─────────────────────────────────────────────────────────────────
const COMPLIANCE_GAUGES = [
  {
    id: 'nist',
    label: 'NIST 800-171',
    score: 87,
    delta: +2,
    controls_pass: 96,
    controls_fail: 8,
    controls_total: 110,
    color: '#3B6FE3',
  },
  {
    id: 'cmmc',
    label: 'CMMC 2.0 Level 3',
    score: 79,
    delta: -1,
    controls_pass: 51,
    controls_fail: 13,
    controls_total: 110,
    color: '#D84C7F',
  },
];

const CONTROL_FAMILIES = [
  { id: 'AC', name: 'Access Control',           total: 22, pass: 20, delta: 0 },
  { id: 'AU', name: 'Audit & Accountability',   total: 9,  pass: 8,  delta: +1 },
  { id: 'CM', name: 'Configuration Mgmt',        total: 9,  pass: 7,  delta: -1 },
  { id: 'IA', name: 'Identification & Auth',     total: 11, pass: 10, delta: 0 },
  { id: 'IR', name: 'Incident Response',         total: 3,  pass: 3,  delta: 0 },
  { id: 'MA', name: 'Maintenance',               total: 6,  pass: 4,  delta: -2 },
  { id: 'MP', name: 'Media Protection',          total: 9,  pass: 9,  delta: 0 },
  { id: 'PE', name: 'Physical Protection',       total: 6,  pass: 6,  delta: 0 },
  { id: 'PS', name: 'Personnel Security',        total: 2,  pass: 2,  delta: 0 },
  { id: 'RA', name: 'Risk Assessment',           total: 3,  pass: 2,  delta: 0 },
  { id: 'CA', name: 'Security Assessment',       total: 4,  pass: 3,  delta: 0 },
  { id: 'SC', name: 'System & Comms Protection', total: 16, pass: 13, delta: -1 },
  { id: 'SI', name: 'System & Info Integrity',   total: 7,  pass: 6,  delta: +1 },
  { id: 'SR', name: 'Supply Chain Risk Mgmt',    total: 3,  pass: 2,  delta: 0 },
];

const AUDITOR_FEED = [
  { id: 'AU-001', control: '3.3.1', family: 'AU', status: 'fail',  finding: 'Log retention for OT network does not meet 90-day requirement.', ts: '22:28:11' },
  { id: 'AU-002', control: '3.14.6', family: 'SI', status: 'pass', finding: 'Continuous monitoring via QUILL-TRIAGE verified.', ts: '22:27:44' },
  { id: 'AU-003', control: '3.1.2',  family: 'AC', status: 'pass', finding: 'Least-privilege enforcement confirmed on AD OU=Manufacturing.', ts: '22:26:59' },
  { id: 'AU-004', control: '3.13.5', family: 'SC', status: 'warn', finding: 'DMZ-to-OT firewall ruleset has 3 overly permissive allow rules.', ts: '22:25:33' },
  { id: 'AU-005', control: '3.7.4',  family: 'MA', status: 'fail', finding: 'Unauthorized maintenance on PLC-PROD-03 — no ticket found.', ts: '22:24:01' },
  { id: 'AU-006', control: '3.13.1', family: 'SC', status: 'pass', finding: 'Network segmentation between IT/OT verified via GAGGLE-SCOUT.', ts: '22:22:18' },
];

const NARRATOR_SUMMARY = `Executive Summary — Week of March 16, 2026

The Security Operations Center has maintained continuous surveillance across all Primary and Secondary AI agents with an overall uptime of 99.6%.

During this reporting period, the most critical incident involves an active COBALT STRIKE intrusion targeting DC-01 (INC-2026-041). QUILL-INVESTIGATOR has completed Chain-of-Thought analysis with 95% confidence, attributing the attack to TTPs consistent with APT29. Estimated business risk: $88,400 per hour of dwell time.

CMMC 2.0 Level 3 compliance stands at 79%, a slight decrease of -1% from last week, primarily driven by new findings in System & Communications Protection (SC). Three corrective actions are recommended (see Governor Control Feed).

Supply chain posture remains GREEN. QUILL-VANGUARD has scanned 14 new SBOM submissions this week with zero critical zero-day findings.

RECOMMENDED BOARD ACTIONS:
1. Approve immediate isolation of DC-01 and Switch-04 (HITL pending).
2. Allocate resources to close SC-family control gaps before Q2 CMMC audit.
3. Review vendor access logs for any unauthorized Modbus connections to OT-layer.`;

// ── Radial Gauge ──────────────────────────────────────────────────────────────
function RadialGauge({ score, color, label, delta, passCount, total }) {
  const R = 52;
  const circ = 2 * Math.PI * R;
  const pct = score / 100;
  const dash = pct * circ;
  const gap = circ - dash;

  const deltaColor = delta > 0 ? '#88C057' : delta < 0 ? '#EF4444' : '#6B7280';
  const deltaLabel = delta > 0 ? `+${delta}%` : delta < 0 ? `${delta}%` : '0%';

  return (
    <div className="flex flex-col items-center p-6 rounded-xl"
      style={{ background: '#111827', border: '1px solid #1F2937' }}>
      <svg width={130} height={130} viewBox="0 0 130 130">
        {/* Track */}
        <circle cx={65} cy={65} r={R} fill="none" stroke="#1F2937" strokeWidth={10} />
        {/* Progress */}
        <circle
          cx={65} cy={65} r={R}
          fill="none" stroke={color} strokeWidth={10}
          strokeLinecap="round"
          strokeDasharray={`${dash} ${gap}`}
          strokeDashoffset={circ * 0.25}
          style={{ transition: 'stroke-dasharray 1s ease', filter: `drop-shadow(0 0 6px ${color}88)` }}
        />
        {/* Score text */}
        <text x={65} y={61} textAnchor="middle" dominantBaseline="middle"
          fill="#E2E8F0" style={{ fontSize: 24, fontWeight: 'bold', fontFamily: 'JetBrains Mono' }}>
          {score}%
        </text>
        <text x={65} y={79} textAnchor="middle"
          fill={deltaColor} style={{ fontSize: 10, fontFamily: 'JetBrains Mono' }}>
          {deltaLabel} ▲
        </text>
      </svg>
      <p className="text-xs font-bold mt-1" style={{ color }}>{label}</p>
      <p className="text-xs terminal mt-0.5" style={{ color: '#6B7280' }}>
        {passCount} / {total} controls passing
      </p>
    </div>
  );
}

function ControlFamilyRow({ fam }) {
  const pct = Math.round((fam.pass / fam.total) * 100);
  const color = pct === 100 ? '#88C057' : pct >= 80 ? '#3B6FE3' : pct >= 60 ? '#E5A862' : '#EF4444';
  const deltaColor = fam.delta > 0 ? '#88C057' : fam.delta < 0 ? '#EF4444' : '#374151';
  return (
    <div className="flex items-center gap-3 py-2 border-b" style={{ borderColor: '#1F2937' }}>
      <span className="text-xs terminal font-bold flex-shrink-0" style={{ color, minWidth: 28 }}>{fam.id}</span>
      <span className="text-xs flex-1 truncate" style={{ color: '#9CA3AF' }}>{fam.name}</span>
      <div className="h-1 rounded-full overflow-hidden flex-shrink-0" style={{ background: '#1F2937', width: 80 }}>
        <div className="h-full rounded-full" style={{ width: `${pct}%`, background: color, transition: 'width 1s ease' }} />
      </div>
      <span className="text-xs terminal flex-shrink-0" style={{ color, minWidth: 34 }}>{pct}%</span>
      <span className="text-xs terminal flex-shrink-0" style={{ color: deltaColor, minWidth: 28 }}>
        {fam.delta > 0 ? `+${fam.delta}` : fam.delta < 0 ? `${fam.delta}` : '—'}
      </span>
    </div>
  );
}

function AuditorEntry({ entry }) {
  const statusCfg = {
    pass: { icon: CheckCircle, color: '#88C057' },
    fail: { icon: XCircle,    color: '#EF4444' },
    warn: { icon: AlertCircle, color: '#E5A862' },
  };
  const { icon: Icon, color } = statusCfg[entry.status] || statusCfg.warn;
  return (
    <div className="flex items-start gap-3 py-2.5 border-b" style={{ borderColor: '#1F2937' }}>
      <Icon size={13} style={{ color, flexShrink: 0, marginTop: 1 }} />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-0.5">
          <span className="text-xs terminal font-bold" style={{ color }}>{entry.control}</span>
          <span className="text-xs terminal px-1.5 py-0.5 rounded"
            style={{ background: '#FFFFFF08', color: '#6B7280', border: '1px solid #1F2937' }}>
            {entry.family}
          </span>
        </div>
        <p className="text-xs" style={{ color: '#9CA3AF', lineHeight: 1.5 }}>{entry.finding}</p>
      </div>
      <span className="text-xs terminal flex-shrink-0" style={{ color: '#374151' }}>{entry.ts}</span>
    </div>
  );
}

// ── Main Component ─────────────────────────────────────────────────────────────
export default function GovernanceDashboard() {
  const [narratorExpanded, setNarratorExpanded] = useState(false);
  const [familyExpanded, setFamilyExpanded] = useState(true);

  return (
    <div className="flex flex-col h-full" style={{ background: '#0B1117' }}>
      {/* Header */}
      <div className="flex items-center gap-3 px-5 py-3 border-b flex-shrink-0"
        style={{ borderColor: '#1F2937', background: '#0d1117' }}>
        <Shield size={14} style={{ color: '#A78BFA' }} />
        <span className="text-xs font-bold tracking-widest" style={{ color: '#E2E8F0' }}>
          GOVERNANCE & COMPLIANCE
        </span>
        <span className="text-xs terminal ml-2" style={{ color: '#6B7280' }}>
          FLYWAY-GOVERNOR · FLYWAY-COMMUNICATOR
        </span>
      </div>

      <div className="flex flex-1 min-h-0">
        {/* LEFT: Gauges + Control Families */}
        <div className="flex flex-col overflow-y-auto" style={{ flex: '0 0 55%', minWidth: 360, borderRight: '1px solid #1F2937' }}>
          {/* Compliance Gauges */}
          <div className="p-5 border-b flex-shrink-0" style={{ borderColor: '#1F2937' }}>
            <p className="text-xs terminal mb-4" style={{ color: '#4B5563' }}>COMPLIANCE POSTURE — REAL TIME</p>
            <div className="grid grid-cols-2 gap-4">
              {COMPLIANCE_GAUGES.map(g => (
                <RadialGauge
                  key={g.id}
                  score={g.score}
                  color={g.color}
                  label={g.label}
                  delta={g.delta}
                  passCount={g.controls_pass}
                  total={g.controls_total}
                />
              ))}
            </div>
          </div>

          {/* Control Family Breakdown */}
          <div className="flex-1 overflow-y-auto px-5 py-4">
            <button
              onClick={() => setFamilyExpanded(v => !v)}
              className="flex items-center gap-2 mb-3 w-full">
              <span className="text-xs terminal font-bold" style={{ color: '#6B7280' }}>
                NIST 800-171 CONTROL FAMILY BREAKDOWN
              </span>
              {familyExpanded
                ? <ChevronDown size={12} style={{ color: '#4B5563' }} />
                : <ChevronRight size={12} style={{ color: '#4B5563' }} />}
            </button>
            {familyExpanded && (
              <div>
                <div className="flex items-center gap-3 pb-1 border-b mb-1" style={{ borderColor: '#1F2937' }}>
                  <span className="text-xs terminal flex-shrink-0" style={{ color: '#374151', minWidth: 28 }}>ID</span>
                  <span className="text-xs terminal flex-1" style={{ color: '#374151' }}>FAMILY</span>
                  <span className="text-xs terminal flex-shrink-0" style={{ color: '#374151', minWidth: 80 }}>COVERAGE</span>
                  <span className="text-xs terminal flex-shrink-0" style={{ color: '#374151', minWidth: 34 }}>%</span>
                  <span className="text-xs terminal flex-shrink-0" style={{ color: '#374151', minWidth: 28 }}>Δ</span>
                </div>
                {CONTROL_FAMILIES.map(f => <ControlFamilyRow key={f.id} fam={f} />)}
              </div>
            )}
          </div>
        </div>

        {/* RIGHT: Auditor Feed + Narrator */}
        <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
          {/* Governor Control Feed */}
          <div className="flex flex-col" style={{ flex: '0 0 55%', borderBottom: '1px solid #1F2937' }}>
            <div className="flex items-center gap-2 px-4 py-2.5 border-b flex-shrink-0"
              style={{ borderColor: '#1F2937' }}>
              <BookOpen size={12} style={{ color: '#3B6FE3' }} />
              <span className="text-xs terminal font-bold" style={{ color: '#6B7280' }}>GOVERNOR CONTROL FEED</span>
              <span className="ml-auto text-xs terminal"
                style={{ color: '#EF4444' }}>
                {AUDITOR_FEED.filter(e => e.status === 'fail').length} failures
              </span>
            </div>
            <div className="flex-1 overflow-y-auto px-4">
              {AUDITOR_FEED.map(e => <AuditorEntry key={e.id} entry={e} />)}
            </div>
          </div>

          {/* Communicator Summary */}
          <div className="flex flex-col" style={{ flex: '1 1 45%' }}>
            <button
              onClick={() => setNarratorExpanded(v => !v)}
              className="flex items-center gap-2 px-4 py-2.5 border-b hover:bg-white/5 transition-colors"
              style={{ borderColor: '#1F2937' }}>
              <FileText size={12} style={{ color: '#A78BFA' }} />
              <span className="text-xs terminal font-bold" style={{ color: '#6B7280' }}>
                FLYWAY-COMMUNICATOR — EXECUTIVE SUMMARY
              </span>
              <span className="ml-auto text-xs terminal"
                style={{ color: '#A78BFA' }}>AI-GENERATED</span>
              {narratorExpanded
                ? <ChevronDown size={12} style={{ color: '#4B5563' }} />
                : <ChevronRight size={12} style={{ color: '#4B5563' }} />}
            </button>

            {narratorExpanded ? (
              <div className="flex-1 overflow-y-auto px-4 py-3">
                <pre className="text-xs leading-relaxed whitespace-pre-wrap" style={{ color: '#9CA3AF', fontFamily: 'inherit' }}>
                  {NARRATOR_SUMMARY}
                </pre>
                <div className="flex gap-2 mt-4">
                  <button className="text-xs terminal px-3 py-1.5 rounded hover:brightness-125 transition-all"
                    style={{ background: '#A78BFA22', color: '#A78BFA', border: '1px solid #A78BFA33' }}>
                    Export as PDF
                  </button>
                  <button className="text-xs terminal px-3 py-1.5 rounded hover:brightness-125 transition-all"
                    style={{ background: '#3B6FE322', color: '#3B6FE3', border: '1px solid #3B6FE333' }}>
                    Send to Board
                  </button>
                </div>
              </div>
            ) : (
              <div className="px-4 py-3">
                <p className="text-xs italic" style={{ color: '#4B5563' }}>
                  Click to expand board-level executive summary…
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
