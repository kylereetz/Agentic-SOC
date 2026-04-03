import React from 'react';
import { SkipBack, SkipForward, Play, Pause, Clock, Bot, Shield } from 'lucide-react';
import { useSOC } from '../store/SOCContext';
import AutonomyWidget from './AutonomyWidget';

export default function BottomDock() {
  const {
    replayPlaying, setReplayPlaying,
    replayProgress, setReplayProgress,
    agents, pendingActions, autonomy,
    setApprovalAction, approvalAction,
  } = useSOC();

  const handleSlider = (e) => setReplayProgress(Number(e.target.value));
  const activeAgents = agents.filter(a => a.status === 'ACTIVE').length;
  const firstPending = pendingActions[0];

  // Replay window: 2h 45m ending at the real current time.
  const WINDOW_MS = (2 * 60 * 60 + 45 * 60) * 1000;
  const windowEnd   = new Date();
  const windowStart = new Date(windowEnd.getTime() - WINDOW_MS);

  const formatUTC = (d) => d.toISOString().replace('T', ' ').slice(0, 19) + ' UTC';

  const currentTimestamp = (() => {
    const t = new Date(windowStart.getTime() + (replayProgress / 100) * WINDOW_MS);
    return formatUTC(t);
  })();

  return (
    <div className="flex items-center gap-3 px-3 h-full border-t"
      style={{ background: '#0d1117', borderColor: '#1F2937' }}>

      {/* Playback Controls */}
      <div className="flex items-center gap-1.5 flex-shrink-0">
        <button className="p-1.5 rounded hover:bg-white/5 transition-colors" onClick={() => setReplayProgress(p => Math.max(0, p - 5))}>
          <SkipBack size={13} style={{ color: '#6B7280' }} />
        </button>
        <button
          onClick={() => setReplayPlaying(v => !v)}
          className="w-8 h-8 rounded-full flex items-center justify-center transition-all flex-shrink-0"
          style={{ background: '#3B6FE3', boxShadow: replayPlaying ? '0 0 12px rgba(59,111,227,0.6)' : 'none' }}>
          {replayPlaying ? <Pause size={13} style={{ color: 'white' }} /> : <Play size={13} style={{ color: 'white' }} />}
        </button>
        <button className="p-1.5 rounded hover:bg-white/5 transition-colors" onClick={() => setReplayProgress(p => Math.min(100, p + 5))}>
          <SkipForward size={13} style={{ color: '#6B7280' }} />
        </button>
      </div>

      {/* Timestamp */}
      <div className="flex items-center gap-1.5 terminal text-xs flex-shrink-0" style={{ color: '#6B7280' }}>
        <Clock size={10} />
        <span className="hidden sm:inline">T-MINUS</span>
        {replayPlaying ? <span style={{ color: '#88C057' }}>LIVE</span> : <span>{Math.round((1 - replayProgress / 100) * 123)}m</span>}
      </div>

      {/* Slider */}
      <div className="flex-1 flex flex-col gap-0.5 min-w-0">
        <input
          type="range" min="0" max="100" value={replayProgress} onChange={handleSlider}
          className="w-full h-1.5 rounded-full appearance-none cursor-pointer"
          style={{ background: `linear-gradient(to right, #3B6FE3 ${replayProgress}%, #1F2937 ${replayProgress}%)`, accentColor: '#3B6FE3' }}
        />
        <div className="flex justify-between text-xs terminal" style={{ color: '#4B5563' }}>
          <span>{formatUTC(windowStart)}</span>
          <span style={{ color: '#3B6FE3' }}>CURRENT: {currentTimestamp}</span>
          <span>REALTIME</span>
        </div>
      </div>

      {/* Live stats */}
      <div className="flex items-center gap-3 flex-shrink-0">
        <div className="text-center hidden lg:block">
          <p className="text-xs terminal" style={{ color: '#6B7280' }}>LIVE EVENTS</p>
          <p className="text-sm font-bold" style={{ color: '#EF4444' }}>14.2k <span className="text-xs font-normal">EPS</span></p>
        </div>
        <div className="w-px h-6 hidden lg:block" style={{ background: '#1F2937' }} />
        <div className="text-center hidden lg:block">
          <p className="text-xs terminal" style={{ color: '#6B7280' }}>AGENTS ACTIVE</p>
          <p className="text-sm font-bold" style={{ color: '#88C057' }}>{activeAgents}/{agents.length}</p>
        </div>

        {/* Pending approval badge */}
        {pendingActions.length > 0 && (
          <>
            <div className="w-px h-6" style={{ background: '#1F2937' }} />
            <button
              onClick={() => firstPending && setApprovalAction(firstPending)}
              className="flex items-center gap-1.5 text-xs terminal px-2 py-1 rounded hover:brightness-125 transition-all animate-pulse"
              style={{ background: '#E5A86218', color: '#E5A862', border: '1px solid #E5A86244' }}>
              <Shield size={11} />
              {pendingActions.length} PENDING
            </button>
          </>
        )}

        <div className="w-px h-6" style={{ background: '#1F2937' }} />

        <div className="flex items-center gap-1.5 text-xs terminal" style={{ color: '#D84C7F' }}>
          <Bot size={12} className="animate-pulse" />
          <span>SENTINEL-ORCHESTRATOR ACTIVE</span>
        </div>
      </div>
    </div>
  );
}
