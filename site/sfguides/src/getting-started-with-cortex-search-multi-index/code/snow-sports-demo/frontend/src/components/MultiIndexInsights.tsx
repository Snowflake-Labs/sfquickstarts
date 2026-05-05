import { X } from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Cell,
  ResponsiveContainer,
  LabelList,
} from 'recharts';
import type { MultiSearchResponse } from '../api';

interface MultiIndexInsightsProps {
  data: MultiSearchResponse;
  onClear: () => void;
}

export default function MultiIndexInsights({ data, onClear }: MultiIndexInsightsProps) {
  const chartData = Object.entries(data.index_breakdown).map(([, val]) => ({
    name: val.label,
    count: val.count,
    fill: val.color,
  }));

  return (
    <div className="bg-white rounded-xl shadow border border-slate-100 p-4 text-sm">
      {/* Query + clear */}
      <div className="flex items-start justify-between gap-2 mb-3">
        <div>
          <div className="text-xs text-slate-400">Cortex Search</div>
          <div className="font-semibold text-slate-800 text-sm truncate max-w-[140px]">
            &ldquo;{data.query}&rdquo;
          </div>
          <div className="text-xs text-slate-400 mt-0.5">
            {data.total_results} results
          </div>
        </div>
        <button
          onClick={onClear}
          className="text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded p-1 transition-colors shrink-0"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Index pills */}
      <div className="flex flex-col gap-1.5 mb-3">
        {Object.entries(data.index_breakdown).map(([key, val]) => (
          <div key={key} className="flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <span
                className="w-2 h-2 rounded-full shrink-0"
                style={{ backgroundColor: val.color }}
              />
              <span className="text-xs text-slate-600">{val.label}</span>
            </div>
            <span className="text-xs font-semibold text-slate-700">{val.count}</span>
          </div>
        ))}
      </div>

      {/* Bar chart */}
      {chartData.length > 0 && (
        <div style={{ height: chartData.length * 28 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={chartData}
              layout="vertical"
              margin={{ top: 0, right: 24, left: 0, bottom: 0 }}
            >
              <XAxis type="number" hide />
              <YAxis
                type="category"
                dataKey="name"
                width={72}
                tick={{ fontSize: 11, fill: '#94A3B8' }}
                axisLine={false}
                tickLine={false}
              />
              <Bar dataKey="count" radius={3} maxBarSize={14}>
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.fill} />
                ))}
                <LabelList
                  dataKey="count"
                  position="right"
                  style={{ fontSize: 11, fill: '#475569', fontWeight: 600 }}
                />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
