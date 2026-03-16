import React from 'react';
import { Bot, TrendingUp, Shield, Users } from 'lucide-react';
import { useSOC } from '../store/SOCContext';

function StatRow({ label, value, color }) {
  return (
    <div className="flex items-center justify-between text-xs terminal">
      <span style={{ color: '#6B7280' }}>{label}</span>
      <span className="font-bold" style={{ color }}>{value}</span>
    </div>
  );
}

function GaugeArc({ percent, color }) {
  const r = 30;
  const circ = Math.PI * r; // half circle
  const offset = circ - (percent / 100) * circ;
  return (
    <svg width="80" height="44" viewBox="0 0 80 44">
      <path d="M 8 40 A 32 32 0 0 1 72 40" fill="none" stroke="#1F2937" strokeWidth="6" strokeLinecap="round" />
      <path d="M 8 40 A 32 32 0 0 1 72 40" fill="none" stroke={color} strokeWidth="6" strokeLinecap="round"
        strokeDasharray={circ} strokeDashoffset={offset}
        style={{ transition: 'stroke-dashoffset 1s ease' }} />
    </svg>
  );
}

export default function AutonomyWidget() {
  const { autonomy, pendingActions } = useSOC();
  const total = autonomy.agentActions + autonomy.humanApproved + autonomy.humanOverrides;
  const pct = total > 0 ? Math.round((autonomy.agentActions / total) * 100) : autonomy.level;
  const color = pct >= 80 ? '#D84C7F' : pct >= 60 ? '#3B6FE3' : '#88C057';

  return (
    <div className="flex flex-col gap-3 p-3 rounded-lg"
      style={{ background: '#111827', border: '1px solid #1F2937', minWidth: 200 }}>

      {/* Header */}
      <div className="flex items-center gap-2">
        <Bot size={12} style={{ color: '#D84C7F' }} className="animate-pulse" />
        <span className="text-xs font-bold tracking-widest terminal" style={{ color: '#E2E8F0' }}>AUTONOMY</span>
      </div>

      {/* Gauge */}
      <div className="flex flex-col items-center gap-1">
        <div className="relative">
          <GaugeArc percent={pct} color={color} />
          <div className="absolute bottom-0 left-0 right-0 text-center">
            <p className="text-base font-bold" style={{ color }}>{pct}%</p>
          </div>
        </div>
        <p className="text-xs terminal" style={{ color: '#4B5563' }}>AI Autonomy Level</p>
      </div>

      {/* Stats */}
      <div className="space-y-1.5 border-t pt-2" style={{ borderColor: '#1F2937' }}>
        <StatRow label="Agent Actions"    value={autonomy.agentActions}   color="#D84C7F" />
        <StatRow label="Human Approved"   value={autonomy.humanApproved}  color="#88C057" />
        <StatRow label="Human Overrides"  value={autonomy.humanOverrides} color="#EF4444" />
        <StatRow label="Policy Overrides" value={autonomy.policyOverrides} color="#E5A862" />
      </div>

      {/* Pending approvals indicator */}
      {pendingActions.length > 0 && (
        <div className="flex items-center gap-2 p-2 rounded"
          style={{ background: '#E5A86215', border: '1px solid #E5A86233' }}>
          <Shield size={11} style={{ color: '#E5A862' }} />
          <span className="text-xs terminal" style={{ color: '#E5A862' }}>
            {pendingActions.length} pending approval{pendingActions.length > 1 ? 's' : ''}
          </span>
        </div>
      )}
    </div>
  );
}
