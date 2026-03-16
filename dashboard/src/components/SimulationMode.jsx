import React, { useState } from 'react';
import { FlaskConical, Bot, User, TrendingUp, Play, Pause, RotateCcw } from 'lucide-react';
import { ResponsiveContainer, RadialBarChart, RadialBar, AreaChart, Area, CartesianGrid, XAxis, YAxis, Tooltip } from 'recharts';

const SCENARIO_DATA = [
  { time: '10m', ai: 18, human: 4 }, { time: '20m', ai: 31, human: 6 },
  { time: '30m', ai: 48, human: 8 }, { time: '40m', ai: 62, human: 9 },
  { time: '50m', ai: 79, human: 11 }, { time: '60m', ai: 91, human: 12 },
];

const SAVINGS = [{ name: 'Automation', value: 91, fill: '#D84C7F' }];

const SCENARIOS = ['APT-29 Simulation', 'Ransomware Staging', 'Insider Threat', 'Supply Chain Attack'];

export default function SimulationMode() {
  const [running, setRunning] = useState(false);
  const [scenario, setScenario] = useState('APT-29 Simulation');
  const [progress, setProgress] = useState(72);

  const TOOLTIP_STYLE = { backgroundColor: '#111827', border: '1px solid #1F2937', color: '#CBD5E1', fontSize: 11, borderRadius: 6 };

  return (
    <div className="flex flex-col h-full overflow-y-auto" style={{ background: '#0B1117' }}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b flex-shrink-0"
        style={{ borderColor: '#1F2937', background: '#0d1117' }}>
        <div className="flex items-center gap-2">
          <FlaskConical size={14} style={{ color: '#A78BFA' }} />
          <span className="text-xs font-bold tracking-widest" style={{ color: '#E2E8F0' }}>SIMULATION MODE</span>
          <span className="text-xs terminal px-2 py-0.5 rounded"
            style={{ background: '#A78BFA18', color: '#A78BFA', border: '1px solid #A78BFA33' }}>SANDBOX</span>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => setRunning(v => !v)}
            className="flex items-center gap-1.5 text-xs terminal px-3 py-1.5 rounded hover:brightness-125 transition-all"
            style={{ background: running ? '#EF444420' : '#88C05720', color: running ? '#EF4444' : '#88C057', border: `1px solid ${running ? '#EF444433' : '#88C05733'}` }}>
            {running ? <><Pause size={12} /> PAUSE</> : <><Play size={12} /> RUN SIMULATION</>}
          </button>
          <button className="p-1.5 rounded hover:bg-white/5 transition-colors" title="Reset">
            <RotateCcw size={13} style={{ color: '#6B7280' }} />
          </button>
        </div>
      </div>

      <div className="p-4 space-y-4">
        {/* Scenario Selector */}
        <div className="rounded-lg p-4" style={{ background: '#111827', border: '1px solid #1F2937' }}>
          <p className="text-xs terminal mb-3" style={{ color: '#6B7280' }}>SELECT SCENARIO</p>
          <div className="flex flex-wrap gap-2">
            {SCENARIOS.map(s => (
              <button key={s} onClick={() => setScenario(s)}
                className="text-xs terminal px-3 py-1.5 rounded transition-all hover:brightness-125"
                style={{
                  background: scenario === s ? '#A78BFA22' : 'transparent',
                  color: scenario === s ? '#A78BFA' : '#6B7280',
                  border: `1px solid ${scenario === s ? '#A78BFA44' : '#1F2937'}`,
                }}>
                {s}
              </button>
            ))}
          </div>
        </div>

        {/* Stat Cards */}
        <div className="grid grid-cols-3 gap-3">
          {[
            { label: 'AI Actions', value: 91, color: '#D84C7F', icon: Bot },
            { label: 'Human Actions', value: 12, color: '#3B6FE3', icon: User },
            { label: 'Automation Savings', value: '87%', color: '#88C057', icon: TrendingUp },
          ].map(({ label, value, color, icon: Icon }) => (
            <div key={label} className="rounded-lg p-4 flex flex-col gap-2" style={{ background: '#111827', border: '1px solid #1F2937' }}>
              <div className="flex items-center gap-2">
                <Icon size={13} style={{ color }} />
                <p className="text-xs terminal" style={{ color: '#6B7280' }}>{label}</p>
              </div>
              <p className="text-2xl font-bold" style={{ color }}>{value}</p>
            </div>
          ))}
        </div>

        {/* Progress Chart */}
        <div className="rounded-lg p-4" style={{ background: '#111827', border: '1px solid #1F2937' }}>
          <p className="text-xs terminal mb-3" style={{ color: '#6B7280' }}>SIMULATION TIMELINE — AI vs Human Actions</p>
          <ResponsiveContainer width="100%" height={160}>
            <AreaChart data={SCENARIO_DATA}>
              <defs>
                <linearGradient id="aiGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#D84C7F" stopOpacity={0.4} />
                  <stop offset="100%" stopColor="#D84C7F" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" />
              <XAxis dataKey="time" tick={{ fill: '#4B5563', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#4B5563', fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={TOOLTIP_STYLE} />
              <Area type="monotone" dataKey="ai" stroke="#D84C7F" fill="url(#aiGrad)" strokeWidth={2} name="AI Actions" />
              <Area type="monotone" dataKey="human" stroke="#3B6FE3" fill="transparent" strokeWidth={2} strokeDasharray="4 2" name="Human Actions" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Automation Savings Radial */}
        <div className="rounded-lg p-4 flex flex-col items-center" style={{ background: '#111827', border: '1px solid #1F2937' }}>
          <p className="text-xs terminal mb-2" style={{ color: '#6B7280' }}>AUTOMATION SAVINGS RATIO</p>
          <ResponsiveContainer width="100%" height={120}>
            <RadialBarChart cx="50%" cy="100%" innerRadius="60%" outerRadius="100%" startAngle={180} endAngle={0} data={SAVINGS}>
              <RadialBar background={{ fill: '#1F2937' }} dataKey="value" cornerRadius={6} />
            </RadialBarChart>
          </ResponsiveContainer>
          <p className="text-3xl font-bold -mt-8" style={{ color: '#D84C7F' }}>91%</p>
          <p className="text-xs terminal mt-1" style={{ color: '#6B7280' }}>of actions fully automated</p>
        </div>
      </div>
    </div>
  );
}
