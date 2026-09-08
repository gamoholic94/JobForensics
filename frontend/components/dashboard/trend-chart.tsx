 "use client";

import { Card } from "@/components/ui/card";
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from "recharts";

const data = [
  { day: "Oct 1", legit: 250, fraud: 80 }, { day: "Oct 4", legit: 290, fraud: 125 },
  { day: "Oct 7", legit: 230, fraud: 95 }, { day: "Oct 10", legit: 320, fraud: 140 },
  { day: "Oct 13", legit: 260, fraud: 110 }, { day: "Oct 16", legit: 275, fraud: 115 },
  { day: "Oct 19", legit: 340, fraud: 140 }, { day: "Oct 22", legit: 380, fraud: 130 },
  { day: "Oct 25", legit: 345, fraud: 150 }, { day: "Oct 28", legit: 365, fraud: 110 },
  { day: "Oct 31", legit: 310, fraud: 125 },
];

export function TrendChart() {
  return (
    <Card className="p-5">
      <div className="mb-5">
        <h2 className="text-lg font-bold">Job Posting Trends</h2>
        <p className="text-sm text-[var(--muted)]">Daily analysis of legitimate vs fraudulent postings.</p>
      </div>
      <div className="h-[310px]">
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
      </div>
    </Card>
  );
}
