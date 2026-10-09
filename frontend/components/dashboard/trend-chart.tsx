 "use client";

import { Card } from "@/components/ui/card";
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from "recharts";

export function TrendChart({ data }: { data: Array<{ day: string; legit: number; fraud: number }> }) {
  return (
    <Card className="p-5">
      <div className="mb-5">
        <h2 className="text-lg font-bold">Job Posting Trends</h2>
        <p className="text-sm text-[var(--muted)]">Daily analysis of legitimate vs fraudulent postings.</p>
      </div>
      {data.length === 0 ? <p className="flex h-[310px] items-center justify-center text-sm text-[var(--muted)]">Saved investigations will appear here as trend data.</p> : <div className="h-[310px]">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" />
            <XAxis dataKey="day" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip />
            <Legend />
            <Area type="monotone" dataKey="legit" name="Legitimate" stroke="#12b76a" fill="#12b76a" fillOpacity={0.12} strokeWidth={2} />
            <Area type="monotone" dataKey="fraud" name="Fraudulent" stroke="#f04438" fill="#f04438" fillOpacity={0.08} strokeWidth={2} />
          </AreaChart>
        </ResponsiveContainer>
      </div>}
    </Card>
  );
}
