"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, CheckCircle2, ExternalLink } from "lucide-react";
import { Card } from "@/components/ui/card";
import type { BatchPrediction } from "@/lib/api";

export function BatchAnalysisResult() {
  const [batch, setBatch] = useState<BatchPrediction | null>(null);

  useEffect(() => {
    const stored = sessionStorage.getItem("jobforensics-batch-result");
    if (stored) setBatch(JSON.parse(stored) as BatchPrediction);
  }, []);

  if (!batch) return <Card className="mx-auto max-w-4xl p-8">No batch analysis is available.</Card>;

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div>
        <p className="text-sm font-semibold text-[#315fce]">Batch analysis</p>
        <h1 className="mt-1 text-3xl font-bold tracking-tight">{batch.completed} of {batch.total} jobs checked</h1>
        <p className="mt-2 text-sm text-[var(--muted)]">Review each posting before applying. Failed rows can be corrected and uploaded again.</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <Card className="p-5"><p className="text-sm text-[var(--muted)]">Total links</p><p className="mt-1 text-2xl font-bold">{batch.total}</p></Card>
        <Card className="p-5"><p className="text-sm text-[var(--muted)]">Completed</p><p className="mt-1 text-2xl font-bold text-emerald-600">{batch.completed}</p></Card>
        <Card className="p-5"><p className="text-sm text-[var(--muted)]">Failed</p><p className="mt-1 text-2xl font-bold text-amber-600">{batch.failed}</p></Card>
      </div>

      <Card className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[700px] text-left text-sm">
            <thead className="border-b border-[var(--border)] bg-black/[.02] dark:bg-white/[.03]"><tr><th className="px-5 py-3">Row</th><th className="px-5 py-3">Posting</th><th className="px-5 py-3">Classification</th><th className="px-5 py-3">Risk</th><th className="px-5 py-3">Status</th></tr></thead>
            <tbody>
              {batch.results.map(item => {
                const result = item.result;
                return <tr key={item.row} className="border-b border-[var(--border)] last:border-0">
                  <td className="px-5 py-4 text-[var(--muted)]">{item.row}</td>
                  <td className="max-w-[330px] px-5 py-4"><a href={item.url} target="_blank" rel="noreferrer" className="flex items-center gap-2 truncate font-medium hover:text-[#315fce]" title={item.url}>{result?.job.title || item.url}<ExternalLink size={14} className="shrink-0" /></a></td>
                  <td className="px-5 py-4 font-semibold">{result?.classification || "Unavailable"}</td>
                  <td className="px-5 py-4">{result ? `${Math.round(result.risk.overall_risk_score)}/100` : "-"}</td>
                  <td className="px-5 py-4">{result ? <span className="flex items-center gap-2 text-emerald-600"><CheckCircle2 size={16} /> Checked</span> : <span className="flex items-center gap-2 text-amber-600" title={item.error}><AlertTriangle size={16} /> Failed</span>}</td>
                </tr>;
              })}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}