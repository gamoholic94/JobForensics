 "use client";

import { Card } from "@/components/ui/card";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from "recharts";

const data = [
  { category: "Software", fraud: 18 }, { category: "Data", fraud: 12 },
  { category: "Marketing", fraud: 29 }, { category: "Sales", fraud: 34 },
  { category: "Support", fraud: 41 }, { category: "Finance", fraud: 26 },
];

export function Analytics() {
  return <div className="space-y-6">
    <div><p className="text-sm font-semibold text-[#315fce]">Model Insights</p><h1 className="mt-1 text-3xl font-bold">Analytics</h1><p className="mt-2 text-sm text-[var(--muted)]">Understand model performance and fraud patterns.</p></div>
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">{[["Accuracy","94.2%"],["Precision","92.8%"],["Recall","91.6%"],["F1 Score","92.2%"]].map(([a,b]) => <Card key={a} className="p-5"><div className="text-sm text-[var(--muted)]">{a}</div><div className="mt-2 text-3xl font-bold">{b}</div></Card>)}</div>
    <div className="grid gap-5 lg:grid-cols-2">
      <Card className="p-5"><h2 className="font-bold">Fraud rate by category</h2><p className="mt-1 text-sm text-[var(--muted)]">Illustrative dashboard data — connect your real metrics.</p><div className="mt-5 h-[300px]"><ResponsiveContainer width="100%" height="100%"><BarChart data={data}><CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" /><XAxis dataKey="category" tick={{fontSize:11}} /><YAxis tick={{fontSize:11}} /><Tooltip /><Bar dataKey="fraud" name="Fraud rate %" fill="#f04438" radius={[6,6,0,0]} /></BarChart></ResponsiveContainer></div></Card>
      <Card className="p-5"><h2 className="font-bold">Model evaluation</h2><div className="mt-6 space-y-4">{["Confusion matrix", "ROC curve", "Precision / Recall", "Confidence distribution"].map(x => <div key={x} className="rounded-xl border border-[var(--border)] p-4"><div className="font-semibold">{x}</div><p className="mt-1 text-xs text-[var(--muted)]">Placeholder component — wire to your training/evaluation output.</p></div>)}</div></Card>
    </div>
  </div>;
}
