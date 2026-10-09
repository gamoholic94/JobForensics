"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/layout/app-shell";
import { AnalysisResult } from "@/components/analysis/analysis-result";
import { getInvestigation, Prediction } from "@/lib/api";

export default function InvestigationPage({ params }: { params: Promise<{ id: string }> }) {
  const [result, setResult] = useState<Prediction | null>(null);
  const [investigationId, setInvestigationId] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    params
      .then(({ id }) => {
        setInvestigationId(id);
        return getInvestigation(id);
      })
      .then((stored) => {
        if (active) setResult(stored.result);
      })
      .catch((requestError) => {
        if (active) setError(requestError instanceof Error ? requestError.message : "Could not load investigation.");
      });
    return () => {
      active = false;
    };
  }, [params]);

  return (
    <AppShell>
      {error ? <div className="mx-auto max-w-4xl py-12 text-center text-red-600" role="alert">{error}</div> : result ? <><div className="mx-auto max-w-6xl"><a href={`/api/investigations/${encodeURIComponent(investigationId)}/report`} download className="mb-4 inline-flex rounded-xl bg-[#315fce] px-4 py-2.5 text-sm font-semibold text-white">Download HTML report</a></div><AnalysisResult initialResult={result} readOnly /></> : <div className="mx-auto max-w-4xl py-12 text-center text-[var(--muted)]">Loading investigation...</div>}
    </AppShell>
  );
}
