import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SavedInvestigation } from "@/lib/api";

export function RecentPredictions({ investigations }: { investigations: SavedInvestigation[] }) {
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
            {investigations.slice(0, 5).map((item) => {
              const verdict = item.classification === "Likely Fake" ? "fraudulent" : item.classification === "Likely Legitimate" ? "legitimate" : "verification";
              const tone = verdict === "fraudulent" ? "danger" : verdict === "legitimate" ? "success" : "warning";
              return (
              <tr key={item.id} className="border-t border-[var(--border)]">
                <td className="px-5 py-3.5 font-medium"><Link href={`/investigations/${item.id}`} className="hover:text-[#315fce]">{item.title || "Job posting"}</Link></td>
                <td className="px-5 py-3.5 text-[var(--muted)]">{item.company || "Unavailable"}</td>
                <td className="px-5 py-3.5"><Badge tone={tone}>{verdict}</Badge></td>
                <td className="px-5 py-3.5 font-semibold">{item.overall_risk_score == null ? "Unavailable" : `${Math.round(item.overall_risk_score)}/100`}</td>
              </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
