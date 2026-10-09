 "use client";

import { Card } from "@/components/ui/card";
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip } from "recharts";

export function JobDistribution({ data }: { data: Array<{ name: string; value: number; color: string }> }) {
  const total = data.reduce((sum, item) => sum + item.value, 0);
  return (
    <Card className="p-5">
      <h2 className="text-lg font-bold">Job Type Distribution</h2>
      <p className="text-sm text-[var(--muted)]">Distribution of analyzed postings by category.</p>
      <div className="mt-4 flex flex-col items-center gap-3 sm:flex-row">
        <div className="relative h-[250px] w-[250px] shrink-0">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={data} dataKey="value" innerRadius={72} outerRadius={100} paddingAngle={2}>
                {data.map((d) => <Cell key={d.name} fill={d.color} />)}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
          <div className="pointer-events-none absolute inset-0 grid place-items-center text-center">
            <div><div className="text-xl font-bold">{total}</div><div className="text-xs text-[var(--muted)]">Saved Jobs</div></div>
          </div>
        </div>
        <div className="w-full space-y-2 text-xs">
          {data.map((d) => (
            <div key={d.name} className="flex items-center justify-between gap-3">
              <span className="flex min-w-0 items-center gap-2"><span className="size-2.5 shrink-0 rounded-full" style={{ background: d.color }} /> <span className="truncate">{d.name}</span></span>
              <span className="font-semibold">{total ? `${Math.round((d.value / total) * 100)}%` : "0%"}</span>
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
}
