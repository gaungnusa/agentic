import React from 'react';

interface StatCardProps {
  title: string;
  value: string | number;
  subtext: string;
  valueColor?: string;
}

export default function StatCard({ title, value, subtext, valueColor = 'text-slate-900' }: StatCardProps) {
  return (
    <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
      <div className="text-xs text-slate-400 font-semibold uppercase">{title}</div>
      <div className={`text-2xl font-black mt-1 ${valueColor}`}>{value}</div>
      <div className="text-[11px] text-slate-500 mt-1">{subtext}</div>
    </div>
  );
}