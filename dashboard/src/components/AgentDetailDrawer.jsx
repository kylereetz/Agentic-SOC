import React, { useState, useEffect } from 'react';
import { X, Activity, Server, Target, Clock, AlertTriangle, Zap, Terminal } from 'lucide-react';

export default function AgentDetailDrawer({ agentId, onClose }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Close on Escape key
  useEffect(() => {
    const handleEsc = (e) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleEsc);
    return () => window.removeEventListener('keydown', handleEsc);
  }, [onClose]);

  useEffect(() => {
    if (!agentId) return;
    
    setLoading(true);
    setError(null);
    setData(null);

    const fetchTelemetry = async () => {
      try {
        const response = await fetch(`http://localhost:8000/api/agents/${agentId}/telemetry`);
        if (!response.ok) throw new Error('Failed to fetch telemetry');
        const telemetry = await response.json();
        setData(telemetry);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchTelemetry();
    
    // Simulate SSE / silent polling every 5s
    const intervalId = setInterval(fetchTelemetry, 5000);
    return () => clearInterval(intervalId);
  }, [agentId]);

  if (!agentId) return null;

  return (
    <>
      {/* Backdrop */}
      <div 
        className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />
      
      {/* Drawer */}
      <div className="fixed inset-y-0 right-0 z-50 w-96 transform transition-transform duration-300 ease-in-out shadow-2xl flex flex-col"
           style={{ background: '#0B1117', borderLeft: '1px solid #1F2937' }}>
        
        {/* Header */}
        <div className="p-4 border-b flex justify-between items-center bg-[#0d1117]" style={{ borderColor: '#1F2937' }}>
          <div>
            <h2 className="text-lg font-bold" style={{ color: '#E2E8F0' }}>{agentId}</h2>
            <p className="text-xs terminal" style={{ color: '#6B7280' }}>
              {data ? data.role : 'Loading Identity...'}
            </p>
          </div>
          <button 
            onClick={onClose}
            className="p-1 rounded hover:bg-white/10 transition-colors"
            style={{ color: '#9CA3AF' }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-5 pb-20">
          
          {loading && !data ? (
            <div className="space-y-6 animate-pulse">
              <div className="h-20 bg-[#1F2937] rounded-lg"></div>
              <div className="grid grid-cols-2 gap-3">
                <div className="h-24 bg-[#1F2937] rounded-lg"></div>
                <div className="h-24 bg-[#1F2937] rounded-lg"></div>
                <div className="h-24 bg-[#1F2937] rounded-lg col-span-2"></div>
              </div>
            </div>
          ) : error ? (
            <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-center">
              <AlertTriangle className="mx-auto mb-2 text-red-500" size={24} />
              <p className="text-sm text-red-400">CONNECTION LOST</p>
              <p className="text-xs text-red-500/80 mt-1">{error}</p>
            </div>
          ) : (
            data && (
              <div className="space-y-6">
                
                {/* Status & Current Task */}
                <div>
                  <h3 className="text-xs font-bold tracking-widest mb-3" style={{ color: '#6B7280' }}>CURRENT OBJECTIVE</h3>
                  <div className="p-4 rounded-lg border relative overflow-hidden" style={{ background: '#111827', borderColor: '#1F2937' }}>
                    <div className="flex items-center gap-3 mb-3">
                      <div className="relative flex items-center justify-center">
                        <span className="w-3 h-3 rounded-full absolute animate-ping" style={{ background: '#88C057', opacity: 0.5 }}></span>
                        <span className="w-2.5 h-2.5 rounded-full relative z-10" style={{ background: '#88C057' }}></span>
                      </div>
                      <span className="text-xs terminal font-bold tracking-wider" style={{ color: '#88C057' }}>{data.status}</span>
                    </div>
                    
                    <p className="text-sm text-[#E2E8F0] mb-3 leading-relaxed">
                      {data.current_task.description}
                    </p>
                    
                    <div className="flex items-center gap-4 text-xs terminal" style={{ color: '#9CA3AF' }}>
                      <div className="flex items-center gap-1.5 align-middle">
                        <Target size={12} style={{ color: '#D84C7F' }}/>
                        <span className="mt-0.5">{data.current_task.associated_case}</span>
                      </div>
                      <div className="flex items-center gap-1.5 align-middle">
                        <Clock size={12} style={{ color: '#3B6FE3' }}/>
                        <span className="mt-0.5">{new Date(data.current_task.started_at).toLocaleTimeString()}</span>
                      </div>
                    </div>

                    {/* Indeterminate linear loader */}
                    <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#1F2937] overflow-hidden">
                      <div className="h-full bg-[#88C057] w-1/3 animate-[slide_2s_ease-in-out_infinite]"></div>
                    </div>
                  </div>
                </div>

                {/* Metrics */}
                <div>
                  <h3 className="text-xs font-bold tracking-widest mb-3" style={{ color: '#6B7280' }}>PERFORMANCE METRICS</h3>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="p-3 rounded-lg border" style={{ background: '#111827', borderColor: '#1F2937' }}>
                      <div className="flex items-center gap-2 mb-2 text-[#9CA3AF]">
                        <Activity size={12} />
                        <span className="text-xs terminal">Success Rate</span>
                      </div>
                      <p className="text-xl font-bold" style={{ color: '#88C057' }}>{data.stats.success_rate}%</p>
                    </div>
                    
                    <div className="p-3 rounded-lg border" style={{ background: '#111827', borderColor: '#1F2937' }}>
                      <div className="flex items-center gap-2 mb-2 text-[#9CA3AF]">
                        <Zap size={12} />
                        <span className="text-xs terminal">Tokens Burned</span>
                      </div>
                      <p className="text-xl font-bold" style={{ color: '#D84C7F' }}>
                        {(data.stats.tokens_consumed / 1000).toFixed(1)}k
                      </p>
                    </div>

                    <div className="col-span-2 p-3 rounded-lg border flex items-center justify-between" style={{ background: '#111827', borderColor: '#1F2937' }}>
                      <div className="flex items-center gap-2 text-[#9CA3AF]">
                        <Terminal size={12} />
                        <span className="text-xs terminal">Tools Executed Today</span>
                      </div>
                      <p className="text-lg font-bold" style={{ color: '#3B6FE3' }}>{data.stats.tools_executed_today}</p>
                    </div>

                    <div className="col-span-2 p-3 rounded-lg border flex items-center justify-between" style={{ background: '#111827', borderColor: '#1F2937' }}>
                      <div className="flex items-center gap-2 text-[#9CA3AF]">
                        <Server size={12} />
                        <span className="text-xs terminal">Uptime</span>
                      </div>
                      <p className="text-sm font-bold terminal" style={{ color: '#E2E8F0' }}>
                         {Math.floor(data.stats.uptime_seconds / 3600)}h {Math.floor((data.stats.uptime_seconds % 3600) / 60)}m
                      </p>
                    </div>
                  </div>
                </div>

                {/* Event Log */}
                <div>
                  <h3 className="text-xs font-bold tracking-widest mb-3" style={{ color: '#6B7280' }}>RECENT EVENTS</h3>
                  <div className="space-y-2">
                    {data.recent_events.map((evt, idx) => (
                      <div key={idx} className="p-3 rounded border" style={{ background: '#111827', borderColor: '#1F2937' }}>
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs terminal font-bold" style={{ color: '#E5A862' }}>{evt.type}</span>
                          <span className="text-xs terminal text-[#6B7280]">
                            {new Date(evt.timestamp).toLocaleTimeString()}
                          </span>
                        </div>
                        <p className="text-xs text-[#CBD5E1]">{evt.detail}</p>
                      </div>
                    ))}
                  </div>
                </div>

              </div>
            )
          )}
        </div>
      </div>
    </>
  );
}
