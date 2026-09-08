import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const rows = [
  ["Software Engineer", "TechNova Solutions", "legitimate", "96%"],
  ["Data Analyst", "Bright Minds Ltd", "fraudulent", "92%"],
  ["Marketing Executive", "Global Reach", "legitimate", "89%"],
  ["WFH Typist", "Quick Earners", "fraudulent", "94%"],
  ["Financial Advisor", "WealthGrow Inc", "legitimate", "87%"],
];

export function RecentPredictions() {
  return (
    <Card className="overflow-hidden">
      <div className="flex items-center justify-between p-5">
        <div><h2 className="text-lg font-bold">Recent Job Predictions</h2><p className="text-sm text-[var(--muted)]">Latest analyzed postings.</p></div>
        <Link href="/history" className="text-sm font-semibold text-[#315fce]">View all <ArrowUpRight className="inline" size={15} /></Link>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[620px] text-left text-sm">
          <thead className="bg-black/[.025] text-xs text-[var(--muted)] dark:bg-white/[.03]">
            <tr>{["Job Title", "Company", "Prediction", "Confidence"].map(h => <th key={h} className="px-5 py-3 font-semibold">{h}</th>)}</tr>
          </thead>
          <tbody>
            {rows.map(([title, company, verdict, confidence]) => (
              <tr key={title} className="border-t border-[var(--border)]">
                <td className="px-5 py-3.5 font-medium">{title}</td>
                <td className="px-5 py-3.5 text-[var(--muted)]">{company}</td>
                <td className="px-5 py-3.5"><Badge tone={verdict === "fraudulent" ? "danger" : "success"}>{verdict}</Badge></td>
                <td className="px-5 py-3.5 font-semibold">{confidence}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
