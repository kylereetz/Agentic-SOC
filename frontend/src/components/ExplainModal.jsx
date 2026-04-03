import React from 'react';
import { Brain, X, FileText, Shield, Zap, Target } from 'lucide-react';
import { useSOC } from '../store/SOCContext';

const TYPE_COLORS = { THOUGHT: '#D84C7F', ACTION: '#3B6FE3', OBSERVATION: '#88C057' };

export default function ExplainModal() {
  const { explainEvent, setExplainEvent } = useSOC();
  if (!explainEvent) return null;

  const e = explainEvent;
  const typeColor = TYPE_COLORS[e.type] || '#6B7280';

  return (
    <div className="fixed inset-0 z-[150] flex items-center justify-center"
      style={{ background: 'rgba(11,17,23,0.88)', backdropFilter: 'blur(4px)' }}
      onClick={() => setExplainEvent(null)}>
      <div className="w-full max-w-lg rounded-xl overflow-hidden animate-slide-in"
        style={{ background: '#111827', border: `1px solid ${typeColor}44` }}
        onClick={e => e.stopPropagation()}>

        {/* Header */}
        <div className="flex items-center gap-3 px-5 py-4 border-b"
          style={{ borderColor: `${typeColor}33`, background: '#0d1117' }}>
          <Brain size={15} style={{ color: typeColor }} />
          <div>
            <p className="text-xs terminal font-bold" style={{ color: typeColor }}>AI EXPLAINABILITY MODE</p>
            <p className="text-sm font-semibold" style={{ color: '#E2E8F0' }}>Why did {e.agent} make this decision?</p>
          </div>
          <button onClick={() => setExplainEvent(null)} className="ml-auto p-1.5 rounded hover:bg-white/5 transition-colors">
            <X size={14} style={{ color: '#6B7280' }} />
          </button>
        </div>

        {/* Body */}
        <div className="p-5 space-y-4">
          {/* Step type + tool */}
          <div className="flex items-center gap-3">
            <span className="text-xs font-bold terminal px-2.5 py-1 rounded"
              style={{ background: `${typeColor}18`, color: typeColor, border: `1px solid ${typeColor}33` }}>
              {e.type}
            </span>
            {e.tool && (
              <div className="flex items-center gap-1.5 text-xs terminal" style={{ color: '#6B7280' }}>
                <Zap size={11} />
                Tool: <span style={{ color: '#93C5FD' }}>{e.tool}</span>
              </div>
            )}
            {e.duration && (
              <span className="text-xs terminal" style={{ color: '#4B5563' }}>⏱ {e.duration}</span>
            )}
          </div>

          {/* Reasoning text */}
          <div className="rounded-lg p-4" style={{ background: '#0B1117', border: `1px solid ${typeColor}22` }}>
            <p className="text-xs terminal font-bold mb-2" style={{ color: typeColor }}>AGENT REASONING</p>
            <p className="text-sm leading-relaxed" style={{ color: '#CBD5E1' }}>{e.reasoning || e.content}</p>
          </div>

          {/* Metrics grid */}
          <div className="grid grid-cols-3 gap-3">
            {[
              { label: 'Confidence', value: `${e.confidence}%`, color: e.confidence >= 80 ? '#88C057' : '#E5A862', icon: Target },
              { label: 'MITRE TTP',  value: e.mitre || 'N/A',   color: '#D84C7F',  icon: Shield },
              { label: 'Duration',   value: e.duration || '—',   color: '#3B6FE3',  icon: Zap },
            ].map(({ label, value, color, icon: Icon }) => (
              <div key={label} className="rounded-lg p-3" style={{ background: '#111827', border: '1px solid #1F2937' }}>
                <div className="flex items-center gap-1.5 text-xs terminal mb-1" style={{ color: '#6B7280' }}>
                  <Icon size={10} />
                  {label}
                </div>
                <p className="text-sm font-bold" style={{ color }}>{value}</p>
              </div>
            ))}
          </div>

          {/* Evidence used */}
          {e.evidence?.length > 0 && (
            <div>
              <p className="text-xs terminal font-bold mb-2" style={{ color: '#6B7280' }}>EVIDENCE CONSIDERED</p>
              <div className="flex flex-wrap gap-2">
                {e.evidence.map(evid => (
                  <span key={evid} className="text-xs terminal px-2 py-1 rounded"
                    style={{ background: '#D84C7F11', color: '#D84C7F', border: '1px solid #D84C7F33' }}>
                    <FileText size={10} className="inline mr-1" />{evid}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Triggered policy */}
          <div className="flex items-start gap-2 p-3 rounded-lg" style={{ background: '#3B6FE311', border: '1px solid #3B6FE322' }}>
            <Shield size={12} style={{ color: '#3B6FE3', flexShrink: 0, marginTop: 1 }} />
            <div className="text-xs" style={{ color: '#93C5FD' }}>
              <span className="font-bold">TRIGGERED POLICY:</span> AUTONOMOUS_INVESTIGATION_MODE — Agent acted within delegated authority scope (risk &lt; 95). No human approval required.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
