import React from 'react';
import {
  ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis,
  Radar, AreaChart, Area, BarChart, Bar, CartesianGrid,
  XAxis, YAxis, Tooltip, LineChart, Line, PieChart, Pie, Cell
} from 'recharts';
import { TrendingUp, AlertCircle, Target, Clock } from 'lucide-react';

const AUTONOMY_DATA = [
  { month: 'Oct', auto: 68, human: 32 }, { month: 'Nov', auto: 74, human: 26 },
  { month: 'Dec', auto: 79, human: 21 }, { month: 'Jan', auto: 83, human: 17 },
  { month: 'Feb', auto: 87, human: 13 }, { month: 'Mar', auto: 91, human: 9 },
];

const FP_DATA = [
  { week: 'W1', rate: 14 }, { week: 'W2', rate: 11 }, { week: 'W3', rate: 9 },
  { week: 'W4', rate: 7 }, { week: 'W5', rate: 7 }, { week: 'W6', rate: 5 },
];

const AGENT_PERF = [
  { agent: 'SENTINEL', success: 97, tasks: 42 },
  { agent: 'HERALD',   success: 92, tasks: 18 },
  { agent: 'WARDEN',   success: 100, tasks: 5 },
  { agent: 'RECON',    success: 88, tasks: 33 },
  { agent: 'ORACLE',   success: 95, tasks: 7 },
];

const DURATION_DATA = [
  { stage: 'Triage', min: 2, avg: 8, max: 24 },
  { stage: 'Invest.', min: 15, avg: 45, max: 180 },
  { stage: 'Contain.', min: 5, avg: 18, max: 60 },
  { stage: 'Eradicate', min: 10, avg: 35, max: 120 },
  { stage: 'Recovery', min: 30, avg: 90, max: 240 },
];

const PIE_DATA = [
  { name: 'Autonomous', value: 91, color: '#D84C7F' },
  { name: 'Human-Assist', value: 9, color: '#3B6FE3' },
];

const TOOLTIP_STYLE = {
  backgroundColor: '#111827', border: '1px solid #1F2937', color: '#CBD5E1', fontSize: 11, borderRadius: 6
};

function MetricCard({ icon: Icon, label, value, delta, color }) {
  return (
    <div className="rounded-lg p-4" style={{ background: '#111827', border: '1px solid #1F2937' }}>
      <div className="flex items-center justify-between mb-2">
        <p className="h-label" style={{ color: '#6B7280' }}>{label}</p>
        <Icon size={14} style={{ color }} />
      </div>
      <p className="h-stat" style={{ color }}>{value}</p>
      {delta && <p className="h-meta mt-1" style={{ color: '#88C057' }}>{delta}</p>}
    </div>
  );
}

export default function AnalyticsDashboard() {
  return (
    <div className="flex flex-col h-full overflow-y-auto" style={{ background: '#0B1117' }}>
      <div className="flex items-center gap-2 px-4 py-3 border-b flex-shrink-0"
        style={{ borderColor: '#1F2937', background: '#0d1117' }}>
        <TrendingUp size={14} style={{ color: '#88C057' }} />
        <span className="text-xs font-bold tracking-widest" style={{ color: '#E2E8F0' }}>ANALYTICS DASHBOARD</span>
      </div>

      <div className="p-4 space-y-4">
        {/* KPI Cards */}
        <div className="grid grid-cols-4 gap-3">
          <MetricCard icon={Target} label="Autonomy Ratio" value="91%" delta="↑ 4% vs last month" color="#D84C7F" />
          <MetricCard icon={AlertCircle} label="False Positive Rate" value="5.2%" delta="↓ 2.8% vs last month" color="#88C057" />
          <MetricCard icon={TrendingUp} label="Avg Success Rate" value="94.4%" delta="↑ 1.2% vs last month" color="#3B6FE3" />
          <MetricCard icon={Clock} label="Avg Investigation" value="48 min" delta="↓ 12 min vs last month" color="#E5A862" />
        </div>

        {/* Autonomy Trend + Pie */}
        <div className="grid grid-cols-3 gap-3">
          <div className="col-span-2 rounded-lg p-4" style={{ background: '#111827', border: '1px solid #1F2937' }}>
            <p className="text-xs terminal mb-3" style={{ color: '#6B7280' }}>AUTONOMY RATIO TREND</p>
            <ResponsiveContainer width="100%" height={160}>
              <AreaChart data={AUTONOMY_DATA}>
                <defs>
                  <linearGradient id="autoGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#D84C7F" stopOpacity={0.4} />
                    <stop offset="100%" stopColor="#D84C7F" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" />
                <XAxis dataKey="month" tick={{ fill: '#4B5563', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#4B5563', fontSize: 11 }} axisLine={false} tickLine={false} domain={[50, 100]} />
                <Tooltip contentStyle={TOOLTIP_STYLE} />
                <Area type="monotone" dataKey="auto" stroke="#D84C7F" fill="url(#autoGrad)" strokeWidth={2} name="AI Autonomous %" />
                <Area type="monotone" dataKey="human" stroke="#3B6FE3" fill="transparent" strokeWidth={1.5} strokeDasharray="4 2" name="Human Assist %" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <div className="rounded-lg p-4 flex flex-col items-center justify-center" style={{ background: '#111827', border: '1px solid #1F2937' }}>
            <p className="text-xs terminal mb-3" style={{ color: '#6B7280' }}>HUMAN vs AI ACTIONS</p>
            <ResponsiveContainer width="100%" height={140}>
              <PieChart>
                <Pie data={PIE_DATA} cx="50%" cy="50%" innerRadius={40} outerRadius={60} dataKey="value" strokeWidth={0}>
                  {PIE_DATA.map((entry, i) => <Cell key={i} fill={entry.color} />)}
                </Pie>
                <Tooltip contentStyle={TOOLTIP_STYLE} />
              </PieChart>
            </ResponsiveContainer>
            <div className="flex gap-3 text-xs terminal">
              {PIE_DATA.map(d => (
                <div key={d.name} className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full" style={{ background: d.color }} />
                  <span style={{ color: '#6B7280' }}>{d.name}: </span>
                  <span style={{ color: d.color }}>{d.value}%</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* FP Rate + Agent Perf */}
        <div className="grid grid-cols-2 gap-3">
          <div className="rounded-lg p-4" style={{ background: '#111827', border: '1px solid #1F2937' }}>
            <p className="text-xs terminal mb-3" style={{ color: '#6B7280' }}>FALSE POSITIVE RATE (6 weeks)</p>
            <ResponsiveContainer width="100%" height={140}>
              <LineChart data={FP_DATA}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" />
                <XAxis dataKey="week" tick={{ fill: '#4B5563', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#4B5563', fontSize: 11 }} axisLine={false} tickLine={false} unit="%" />
                <Tooltip contentStyle={TOOLTIP_STYLE} />
                <Line type="monotone" dataKey="rate" stroke="#88C057" strokeWidth={2} dot={{ fill: '#88C057', r: 3 }} name="FP Rate" />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div className="rounded-lg p-4" style={{ background: '#111827', border: '1px solid #1F2937' }}>
            <p className="text-xs terminal mb-3" style={{ color: '#6B7280' }}>AGENT SUCCESS RATE</p>
            <ResponsiveContainer width="100%" height={140}>
              <BarChart data={AGENT_PERF} barSize={16}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" />
                <XAxis dataKey="agent" tick={{ fill: '#4B5563', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#4B5563', fontSize: 11 }} axisLine={false} tickLine={false} domain={[80, 100]} unit="%" />
                <Tooltip contentStyle={TOOLTIP_STYLE} />
                <Bar dataKey="success" name="Success %" radius={[3, 3, 0, 0]}>
                  {AGENT_PERF.map((_, i) => (
                    <Cell key={i} fill={['#D84C7F', '#3B6FE3', '#EF4444', '#88C057', '#E5A862'][i]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Duration */}
        <div className="rounded-lg p-4" style={{ background: '#111827', border: '1px solid #1F2937' }}>
          <p className="text-xs terminal mb-3" style={{ color: '#6B7280' }}>AVG INVESTIGATION DURATION BY STAGE (minutes)</p>
          <ResponsiveContainer width="100%" height={120}>
            <BarChart data={DURATION_DATA} barSize={20}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" />
              <XAxis dataKey="stage" tick={{ fill: '#4B5563', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#4B5563', fontSize: 11 }} axisLine={false} tickLine={false} unit="m" />
              <Tooltip contentStyle={TOOLTIP_STYLE} />
              <Bar dataKey="avg" name="Avg Duration" fill="#3B6FE3" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
