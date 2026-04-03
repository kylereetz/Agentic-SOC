import React, { useState, useEffect, useCallback } from 'react';
import { Target, FileText, CheckCircle, AlertTriangle, ShieldCheck, Cpu, ArrowRight } from 'lucide-react';
import { useAuth } from '../store/AuthContext';
import { useSOC } from '../store/SOCContext';

export default function LogIntegrityMonitor() {
  const { token } = useAuth();
  const { setSelectedHost } = useSOC();
  
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchLogStats = useCallback(async () => {
    if (!token) return;
    try {
      const res = await fetch('http://localhost:8000/api/v1/log-guardian', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      setData(json);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch log guardian stats:', err);
      setError('Connection to Log Guardian telemetry failed');
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    fetchLogStats();
    const interval = setInterval(fetchLogStats, 5000); // Live poll
    return () => clearInterval(interval);
  }, [fetchLogStats]);

  if (loading && !data) {
    return (
      <div className="flex flex-col h-full items-center justify-center bg-app">
        <div className="w-8 h-8 rounded-full border-2 border-t-transparent animate-spin" style={{ borderColor: '#88C057', borderTopColor: 'transparent' }} />
        <p className="mt-4 h-meta text-[#6B7280]">Connecting to Log Guardian pipeline...</p>
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="flex flex-col h-full items-center justify-center bg-app">
        <AlertTriangle size={32} color="#EF4444" />
        <p className="mt-4 h-title text-[#EF4444]">{error}</p>
      </div>
    );
  }

  const { metrics, recent_agentic } = data || {};
  const { total_processed = 0, fast_path = 0, llm_fallback = 0, failed = 0 } = metrics || {};
  
  const fastPathPct = total_processed > 0 ? Math.round((fast_path / total_processed) * 100) : 0;
  const llmPct = total_processed > 0 ? Math.round((llm_fallback / total_processed) * 100) : 0;
  const failPct = total_processed > 0 ? Math.round((failed / total_processed) * 100) : 0;

  return (
    <div className="flex flex-col h-full bg-app">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-3 border-b flex-shrink-0 bg-[#0d1117] border-panel">
        <div className="flex items-center gap-3">
          <FileText size={14} style={{ color: '#88C057' }} />
          <span className="text-xs font-bold tracking-widest text-[#E2E8F0]">
            LOG INTEGRITY & NLP NORMALIZATION
          </span>
          <span className="text-xs terminal px-2 py-0.5 rounded-full"
            style={{ background: '#88C05720', color: '#88C057', border: '1px solid #88C05740' }}>
            SENTINEL-LOG-GUARDIAN
          </span>
        </div>
      </div>

      <div className="flex flex-1 min-h-0">
        
        {/* LEFT: KPIs */}
        <div className="flex flex-col w-[35%] border-r border-panel overflow-y-auto p-5">
          <p className="h-label mb-4 text-[#6B7280]">PIPELINE EFFICIENCY</p>
          
          <div className="space-y-4">
            <div className="p-4 rounded-lg border border-panel" style={{ background: '#111827' }}>
              <div className="flex items-center justify-between mb-1">
                <span className="h-label text-[#4B5563]">TOTAL PROCESSED</span>
                <Target size={14} color="#3B6FE3" />
              </div>
              <span className="h-stat" style={{ color: '#3B6FE3' }}>{total_processed.toLocaleString()}</span>
            </div>

            <div className="p-4 rounded-lg border border-panel" style={{ background: '#111827' }}>
              <div className="flex items-center justify-between mb-1">
                <span className="h-label text-[#4B5563]">FAST-PATH REGEX</span>
                <ShieldCheck size={14} color="#88C057" />
              </div>
              <div className="flex items-end gap-3 mb-2">
                <span className="h-stat" style={{ color: '#88C057' }}>{fastPathPct}%</span>
                <span className="h-meta pb-1 text-[#6B7280]">{fast_path.toLocaleString()} logs</span>
              </div>
              <div className="h-1 rounded-full bg-panel">
                <div className="h-full rounded-full" style={{ width: `${fastPathPct}%`, background: '#88C057' }} />
              </div>
            </div>

            <div className="p-4 rounded-lg border border-panel animate-pulse-magenta" style={{ background: '#111827', borderColor: '#D84C7F66' }}>
              <div className="flex items-center justify-between mb-1">
                <span className="h-label text-[#D84C7F]">AGENTIC FALLBACK (LLM)</span>
                <Cpu size={14} color="#D84C7F" />
              </div>
              <div className="flex items-end gap-3 mb-2">
                <span className="h-stat" style={{ color: '#D84C7F' }}>{llmPct}%</span>
                <span className="h-meta pb-1 text-[#D84C7F99]">{llm_fallback.toLocaleString()} logs</span>
              </div>
              <div className="h-1 rounded-full bg-[#D84C7F33]">
                <div className="h-full rounded-full" style={{ width: `${llmPct}%`, background: '#D84C7F', filter: 'drop-shadow(0 0 4px #D84C7F88)' }} />
              </div>
            </div>

            {failPct > 0 && (
              <div className="p-4 rounded-lg border border-[#EF444444]" style={{ background: '#EF444410' }}>
                <div className="flex items-center justify-between mb-1">
                  <span className="h-label text-[#EF4444]">DROP RATE</span>
                  <AlertTriangle size={14} color="#EF4444" />
                </div>
                <div className="flex items-end gap-3">
                  <span className="h-stat text-[#EF4444]">{failPct}%</span>
                  <span className="h-meta pb-1 text-[#EF444488]">{failed.toLocaleString()} dropped</span>
                </div>
              </div>
            )}
          </div>

          <div className="mt-8 p-4 rounded-lg border border-panel bg-[#0B1117]">
             <p className="h-body text-[#9CA3AF] leading-relaxed">
               The <span className="text-[#88C057] font-bold">Fast-Path</span> engine uses pre-compiled regex for known IT assets (Windows, Cisco). 
               The <span className="text-[#D84C7F] font-bold">Agentic Fallback</span> engine dynamically infers schemas for legacy or proprietary OT payloads using a localized LLM.
             </p>
          </div>
        </div>

        {/* RIGHT: Agentic Feed */}
        <div className="flex flex-col flex-1 min-w-0">
          <div className="px-5 py-4 border-b border-panel bg-[#080d14]">
            <p className="h-label text-[#D84C7F] flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-[#D84C7F] animate-blink" />
              AGENTIC NLP EXTRACTION STREAM
            </p>
          </div>
          
          <div className="flex-1 overflow-y-auto p-5 space-y-4 scanline-overlay bg-[#080c12]">
            {(!recent_agentic || recent_agentic.length === 0) ? (
               <div className="flex flex-col h-full items-center justify-center opacity-50 space-y-3">
                 <ShieldCheck size={32} color="#6B7280" />
                 <p className="h-body text-[#6B7280]">All logs normalizing via Fast-Path regex.</p>
               </div>
            ) : (
                recent_agentic.map((log, i) => (
                  <div key={i} className="p-4 rounded-lg border border-panel bg-[#111827] shadow-lg animate-slide-in-up">
                    <div className="flex items-center justify-between mb-3 border-b border-panel pb-2">
                       <span className="h-meta font-bold text-[#E2E8F0]">{log.source}</span>
                       <span className="h-meta flex items-center gap-1">
                          Source IP: <span className="text-[#3B6FE3] hover:underline cursor-pointer" onClick={() => setSelectedHost(log.ip)}>{log.ip}</span>
                       </span>
                    </div>
                    
                    <div className="grid grid-cols-[1fr_40px_1fr] gap-4 items-center">
                       {/* RAW */}
                       <div className="p-3 bg-[#000000] rounded border border-[#1F2937] font-mono text-[10px] text-[#EF4444] break-all leading-relaxed">
                         {log.raw}
                       </div>
                       
                       <div className="flex justify-center flex-col items-center gap-1 opacity-50">
                         <Cpu size={14} color="#D84C7F" />
                         <ArrowRight size={14} color="#D84C7F" />
                       </div>

                       {/* INFERRED */}
                       <div className="p-3 bg-[#D84C7F11] rounded border border-[#D84C7F44] text-xs terminal text-[#E2E8F0] leading-relaxed">
                         <span className="text-[#D84C7F] font-bold">nlp_inference:</span> "{log.inferred}"
                       </div>
                    </div>
                  </div>
                ))
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
