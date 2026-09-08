import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const rows = [
  ["Software Engineer", "TechNova Solutions", "legitimate", "96%", "Sep 08, 2026"],
  ["Data Analyst", "Bright Minds Ltd", "fraudulent", "92%", "Sep 08, 2026"],
  ["Marketing Executive", "Global Reach", "legitimate", "89%", "Sep 07, 2026"],
  ["WFH Typist", "Quick Earners", "fraudulent", "94%", "Sep 07, 2026"],
  ["Financial Advisor", "WealthGrow Inc", "verification", "62%", "Sep 06, 2026"],
];

export function HistoryTable() {
  return <div className="space-y-6">
    <div><p className="text-sm font-semibold text-[#315fce]">Records</p><h1 className="mt-1 text-3xl font-bold">Analysis History</h1><p className="mt-2 text-sm text-[var(--muted)]">Review previously analyzed job postings.</p></div>
    <Card className="overflow-hidden">
      <div className="border-b border-[var(--border)] p-4"><input className="w-full max-w-md rounded-xl border border-[var(--border)] bg-transparent px-3 py-2.5 text-sm outline-none" placeholder="Search history..." /></div>
      <div className="overflow-x-auto"><table className="w-full min-w-[760px] text-left text-sm">
        <thead className="bg-black/[.025] text-xs text-[var(--muted)] dark:bg-white/[.03]"><tr>{["Job", "Company", "Result", "Confidence", "Date"].map(h => <th key={h} className="px-5 py-3 font-semibold">{h}</th>)}</tr></thead>
        <tbody>{rows.map(r => <tr key={r[0]} className="border-t border-[var(--border)]"><td className="px-5 py-4 font-medium">{r[0]}</td><td className="px-5 py-4 text-[var(--muted)]">{r[1]}</td><td className="px-5 py-4"><Badge tone={r[2] === "fraudulent" ? "danger" : r[2] === "legitimate" ? "success" : "warning"}>{r[2]}</Badge></td><td className="px-5 py-4 font-semibold">{r[3]}</td><td className="px-5 py-4 text-[var(--muted)]">{r[4]}</td></tr>)}</tbody>
      </table></div>
    </Card>
  </div>;
}
