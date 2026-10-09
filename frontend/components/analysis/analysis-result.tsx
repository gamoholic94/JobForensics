 "use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AlertTriangle, CheckCircle2, ShieldAlert, ExternalLink, ArrowLeft } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Prediction, saveInvestigation } from "@/lib/api";

export function AnalysisResult({ initialResult, readOnly = false }: { initialResult?: Prediction; readOnly?: boolean }) {
  const [result, setResult] = useState<Prediction | null>(initialResult || null);
  const [saveState, setSaveState] = useState<"idle" | "saving" | "saved" | "error">("idle");

  useEffect(() => {
    if (initialResult) return;
    const raw = sessionStorage.getItem("jobforensics-result");
    if (raw) setResult(JSON.parse(raw));
  }, [initialResult]);

  if (!result) {
    return <div className="mx-auto max-w-4xl py-12 text-center text-[var(--muted)]">No analysis is available. Start with a job posting.</div>;
  }

  const pct = Math.round(result.probability * 100);
  const isFraud = result.prediction === "fraudulent";
  const isLegit = result.prediction === "legitimate";
  const verdict = isFraud
    ? "This job appears fraudulent"
    : isLegit
      ? "This job appears legitimate"
      : "This job cannot be confirmed yet";
  const componentScores = result.risk?.component_scores || {};
  const riskSignals = [
    ["Model signal", "ml"],
    ["Domain signal", "domain"],
    ["Company information", "company"],
    ["Salary claim", "salary"],
    ["Application process", "application"],
    ["Job description", "content"],
  ] as const;
  async function saveCurrentInvestigation() {
    if (!result || saveState === "saving" || saveState === "saved") return;
    setSaveState("saving");
    try {
      await saveInvestigation(result);
      setSaveState("saved");
    } catch {
      setSaveState("error");
    }
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <Link href="/detect" className="inline-flex items-center gap-2 text-sm font-semibold text-[var(--muted)] hover:text-[var(--foreground)]"><ArrowLeft size={16} /> Analyze another job</Link>

      <Card className={`overflow-hidden ${isFraud ? "border-red-200 dark:border-red-900/50" : isLegit ? "border-emerald-200 dark:border-emerald-900/50" : "border-amber-200"}`}>
        <div className={`p-6 lg:p-8 ${isFraud ? "bg-red-50/60 dark:bg-red-950/20" : isLegit ? "bg-emerald-50/60 dark:bg-emerald-950/20" : "bg-amber-50/60"}`}>
          <div className="flex flex-col gap-7 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <Badge tone={isFraud ? "danger" : isLegit ? "success" : "warning"}>
                {isFraud ? "Likely Fraudulent" : isLegit ? "Likely Legitimate" : "Needs Verification"}
              </Badge>
              <h1 className="mt-4 text-3xl font-bold">{verdict}</h1>
              <p className="mt-2 text-lg font-semibold">{result.job?.title || "Job posting"}</p>
              <p className="mt-1 text-[var(--muted)]">{result.job?.company || "Company unavailable"}</p>
              {result.job?.source_url && (
                <a href={result.job.source_url} target="_blank" rel="noreferrer" className="mt-3 inline-flex items-center gap-1 text-sm text-[#315fce]">
                  Job posting <ExternalLink size={14} />
                </a>
              )}
              {!readOnly && <div className="mt-4 flex items-center gap-3">
                <Button onClick={saveCurrentInvestigation} disabled={saveState === "saving" || saveState === "saved"}>
                  {saveState === "saved" ? "Investigation saved" : saveState === "saving" ? "Saving..." : "Save investigation"}
                </Button>
                {saveState === "error" && <span className="text-sm text-red-600" role="alert">Could not save this investigation.</span>}
              </div>}
            </div>
            <div className="text-center">
              <div className={`mx-auto grid size-36 place-items-center rounded-full border-[12px] ${isFraud ? "border-red-200 text-red-600" : isLegit ? "border-emerald-200 text-emerald-600" : "border-amber-200 text-amber-600"}`}>
                <div><div className="text-3xl font-bold">{pct}%</div><div className="text-xs text-[var(--muted)]">fraud likelihood</div></div>
              </div>
            </div>
          </div>
        </div>
      </Card>

      <div className="grid gap-5 lg:grid-cols-[1.2fr_.8fr]">
        <Card className="p-6">
          <div className="flex items-center gap-2"><ShieldAlert className="text-red-500" size={20} /><h2 className="text-lg font-bold">{isFraud ? "Why this job was flagged" : isLegit ? "Why it appears legitimate" : "Why verification is needed"}</h2></div>
          <div className="mt-5 space-y-3">
            {result.reasons?.map((reason: string) => (
              <div key={reason} className="rounded-xl border border-[var(--border)] p-4">
                <div className="flex gap-3">
                  <AlertTriangle size={18} className="mt-0.5 shrink-0 text-red-500" />
                  <div><div className="font-semibold">{reason}</div><p className="mt-1 text-xs leading-5 text-[var(--muted)]">This indicator contributed to the model's overall risk assessment.</p></div>
                </div>
              </div>
            ))}
          </div>
        </Card>

        <Card className="p-6">
          <h2 className="text-lg font-bold">Risk Assessment</h2>
          <p className="mt-1 text-sm text-[var(--muted)]">Signal strength from the available job information.</p>
          <div className="mt-6 space-y-5">
            {riskSignals.map(([label, key]) => {
              const value = Math.round(Math.max(0, Math.min(100, Number(componentScores[key] || 0))));
              const level = value >= 70 ? "High" : value >= 40 ? "Medium" : "Low";
              return (
                <div key={label}>
                  <div className="mb-2 flex justify-between text-sm"><span>{label}</span><span className="font-semibold">{level}</span></div>
                  <div className="h-2 rounded-full bg-slate-100 dark:bg-slate-800"><div className="h-full rounded-full bg-red-500" style={{ width: `${value}%` }} /></div>
                </div>
              );
            })}
          </div>
        </Card>
      </div>

      <Card className="p-6">
        <div className="flex items-start gap-3">
          {isFraud ? <AlertTriangle className="text-red-500" /> : <CheckCircle2 className="text-emerald-500" />}
          <div>
            <h2 className="font-bold">What should you do?</h2>
            <p className="mt-1 text-sm leading-6 text-[var(--muted)]">
              {isFraud
                ? "Do not send money or sensitive documents. Verify the company through its official website and independent sources before taking any further action."
                : "No major fraud indicators were detected by the current model. You should still verify the employer and application channel before sharing sensitive information."}
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
}
