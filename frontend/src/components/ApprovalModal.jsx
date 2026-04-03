import React, { useState } from 'react';
import { Shield, AlertTriangle, X, Check, XCircle, Users, Server } from 'lucide-react';
import { useSOC } from '../store/SOCContext';

const TYPE_LABELS = {
  HOST_ISOLATION:  { label: 'Host Isolation',   color: '#EF4444', icon: Server },
  ACCOUNT_DISABLE: { label: 'Account Disable',  color: '#E5A862', icon: Users },
  FIREWALL_BLOCK:  { label: 'Firewall Block',   color: '#D84C7F', icon: Shield },
};

function RiskMeter({ score }) {
  const color = score >= 80 ? '#EF4444' : score >= 50 ? '#E5A862' : '#88C057';
  return (
    <div>
      <div className="flex items-center justify-between text-xs terminal mb-1">
        <span style={{ color: '#6B7280' }}>Risk Score</span>
        <span className="font-bold" style={{ color }}>{score} / 100</span>
      </div>
      <div className="h-2 rounded-full overflow-hidden" style={{ background: '#1F2937' }}>
        <div className="h-full rounded-full transition-all" style={{ width: `${score}%`, background: color }} />
      </div>
    </div>
  );
}

export default function ApprovalModal() {
  const { approvalAction, setApprovalAction, approveAction, rejectAction } = useSOC();
  const [confirmed, setConfirmed] = useState(false);

  if (!approvalAction) return null;

  const typeInfo = TYPE_LABELS[approvalAction.type] || { label: approvalAction.type, color: '#6B7280', icon: Shield };
  const TypeIcon = typeInfo.icon;

  return (
    <div className="fixed inset-0 z-[150] flex items-center justify-center"
      style={{ background: 'rgba(11,17,23,0.88)', backdropFilter: 'blur(4px)' }}>
      <div className="w-full max-w-lg rounded-xl overflow-hidden animate-slide-in"
        style={{ background: '#111827', border: `1px solid ${typeInfo.color}44`, boxShadow: `0 0 40px ${typeInfo.color}18` }}>

        {/* Header */}
        <div className="flex items-center gap-3 px-5 py-4 border-b"
          style={{ borderColor: `${typeInfo.color}33`, background: '#0d1117' }}>
          <div className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0"
            style={{ background: `${typeInfo.color}22`, border: `1px solid ${typeInfo.color}44` }}>
            <TypeIcon size={17} style={{ color: typeInfo.color }} />
          </div>
          <div>
            <p className="text-xs terminal font-bold" style={{ color: typeInfo.color }}>HUMAN APPROVAL REQUIRED</p>
            <p className="text-sm font-bold" style={{ color: '#E2E8F0' }}>{typeInfo.label}</p>
          </div>
          <div className="ml-auto text-xs terminal px-2 py-0.5 rounded"
            style={{ background: '#FFFFFF08', color: '#6B7280', border: '1px solid #1F2937' }}>
            {approvalAction.agent}
          </div>
          <button onClick={() => setApprovalAction(null)} className="p-1.5 rounded hover:bg-white/5 transition-colors">
            <X size={14} style={{ color: '#6B7280' }} />
          </button>
        </div>

        {/* Body */}
        <div className="p-5 space-y-4">
          {/* Description */}
          <div className="p-3 rounded-lg" style={{ background: '#0B1117', border: '1px solid #1F2937' }}>
            <p className="text-xs terminal mb-1" style={{ color: '#6B7280' }}>ACTION DESCRIPTION</p>
            <p className="text-sm" style={{ color: '#CBD5E1' }}>{approvalAction.description}</p>
          </div>

          {/* Risk meter */}
          <RiskMeter score={approvalAction.risk} />

          {/* Impacted assets */}
          <div>
            <p className="text-xs terminal mb-2" style={{ color: '#6B7280' }}>IMPACTED ASSETS</p>
            <div className="flex flex-wrap gap-2">
              {approvalAction.impacted.map(asset => (
                <span key={asset} className="text-xs terminal px-2.5 py-1 rounded"
                  style={{ background: '#EF444415', color: '#FF9CA3', border: '1px solid #EF444433' }}>
                  {asset}
                </span>
              ))}
            </div>
          </div>

          {/* Warning */}
          <div className="flex items-start gap-2 p-3 rounded-lg"
            style={{ background: '#E5A86211', border: '1px solid #E5A86233' }}>
            <AlertTriangle size={13} style={{ color: '#E5A862', flexShrink: 0, marginTop: 1 }} />
            <p className="text-xs" style={{ color: '#E5A862' }}>
              This action is irreversible in less than 30 seconds. Verify the target before confirming. Policy: <strong>REQUIRE_HUMAN_APPROVAL</strong> (Risk ≥ 70).
            </p>
          </div>

          {/* Actions */}
          {confirmed ? (
            <div className="text-center py-2">
              <p className="text-sm font-bold" style={{ color: '#88C057' }}>✓ Action approved — dispatched to {approvalAction.agent}</p>
              <button onClick={() => { approveAction(approvalAction.id); setConfirmed(false); }}
                className="mt-1 text-xs terminal" style={{ color: '#4B5563' }}>Close</button>
            </div>
          ) : (
            <div className="flex gap-3">
              <button
                onClick={() => setConfirmed(true)}
                className="flex-1 flex items-center justify-center gap-2 text-sm font-bold terminal py-2.5 rounded-lg hover:brightness-125 transition-all"
                style={{ background: `${typeInfo.color}22`, color: typeInfo.color, border: `1px solid ${typeInfo.color}44` }}>
                <Check size={15} /> Approve
              </button>
              <button
                onClick={() => { rejectAction(approvalAction.id); }}
                className="flex-1 flex items-center justify-center gap-2 text-sm terminal py-2.5 rounded-lg hover:brightness-125 transition-all"
                style={{ background: '#FFFFFF08', color: '#6B7280', border: '1px solid #1F2937' }}>
                <XCircle size={15} /> Reject
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
