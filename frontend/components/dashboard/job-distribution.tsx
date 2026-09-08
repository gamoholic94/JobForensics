 "use client";

import { Card } from "@/components/ui/card";
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip } from "recharts";

const data = [
  { name: "Software Development", value: 28.4, color: "#315fce" },
  { name: "Data Science", value: 14.2, color: "#7c5cff" },
  { name: "Marketing", value: 12.1, color: "#12b76a" },
  { name: "Sales", value: 10.8, color: "#f79009" },
  { name: "Customer Support", value: 9.4, color: "#f04438" },
  { name: "Finance", value: 8.7, color: "#facc15" },
  { name: "Others", value: 16.4, color: "#98a2b3" },
];

export function JobDistribution() {
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
            <div><div className="text-xl font-bold">12,486</div><div className="text-xs text-[var(--muted)]">Total Jobs</div></div>
          </div>
        </div>
        <div className="w-full space-y-2 text-xs">
          {data.map((d) => (
            <div key={d.name} className="flex items-center justify-between gap-3">
              <span className="flex min-w-0 items-center gap-2"><span className="size-2.5 shrink-0 rounded-full" style={{ background: d.color }} /> <span className="truncate">{d.name}</span></span>
              <span className="font-semibold">{d.value}%</span>
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
}
