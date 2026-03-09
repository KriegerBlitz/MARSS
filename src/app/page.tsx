"use client";

import React from 'react';
import { TrendingUp, AlertTriangle, Newspaper, Activity } from 'lucide-react';

interface BentoBoxProps {
  title: string;
  children: React.ReactNode;
  icon: React.ElementType;
  span?: string;
}

const Box = ({ title, children, icon: Icon, span = "" }: BentoBoxProps) => (
    <div className={`bg-slate-900 border border-slate-800 rounded-2xl p-5 flex flex-col ${span}`}>
      <div className="flex items-center gap-2 mb-4 text-blue-400">
        <Icon size={18} />
        <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400">{title}</h2>
      </div>
      <div className="flex-1 overflow-hidden">{children}</div>
    </div>
);

export default function Dashboard() {
  return (
      <main className="min-h-screen bg-[#050505] text-slate-200 p-6">
        {/* Top Navigation / Title */}
        <div className="flex justify-between items-end mb-8 border-b border-slate-800 pb-6">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">MACRO-AI TERMINAL</h1>
            <p className="text-slate-500 text-sm font-mono">Status: Connected to Live Market Feed</p>
          </div>
          <div className="text-right">
            <p className="text- xs text-slate-500 uppercase">System Risk</p>
            <p className="text-sm font-bold text-red-500">ELEVATED</p>
          </div>

        </div>

        {/* Bento Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 auto-rows-[160px]">

          {/* Main Graph Space */}
          <Box title="Predictive Market Analysis" icon={TrendingUp} span="md:col-span-3 md:row-span-3">
            <div className="h-full w-full bg-slate-800/20 rounded-xl border border-slate-800 flex items-center justify-center">
              <p className="text-slate-600 animate-pulse text-sm font-mono">Initializing Neural Engine...</p>
            </div>
          </Box>

          {/* Confidence Widget */}
          <Box title="AI Confidence" icon={Activity} span="md:col-span-1 md:row-span-1">
            <div className="flex items-center justify-center h-full">
              <span className="text-5xl font-black text-emerald-500">92<span className="text-xl">%</span></span>
            </div>
          </Box>

          {/* News & Sentiment */}
          <Box title="AI News Analyst" icon={Newspaper} span="md:col-span-1 md:row-span-2">
            <div className="space-y-4 pt-2">
              <div className="p-2 bg-emerald-500/10 border-l-2 border-emerald-500">
                <p className="text-[10px] text-emerald-400 font-bold">BULLISH SENSE</p>
                <p className="text-xs">Fed Rate hold confirmed...</p>
              </div>
              <div className="p-2 bg-red-500/10 border-l-2 border-red-500">
                <p className="text-[10px] text-red-400 font-bold">BEARISH SENSE</p>
                <p className="text-xs">Crude Oil inventory spike...</p>
              </div>
            </div>
          </Box>

          {/* Risk Correlation */}
          <Box title="Asset Correlation" icon={AlertTriangle} span="md:col-span-4 md:row-span-1">
            <div className="flex gap-4 items-center h-full overflow-x-auto pb-2">
              {['TSLA', 'AAPL', 'NVDA', 'BTC', 'GOLD'].map((ticker) => (
                  <div key={ticker} className="min-w-[120px] p-3 bg-slate-800/40 rounded-lg border border-slate-700">
                    <p className="text-[10px] text-slate-500 font-bold">{ticker}</p>
                    <p className="text-sm font-mono">+0.82 Impact</p>
                  </div>
              ))}
            </div>
          </Box>

        </div>
      </main>
  );
}