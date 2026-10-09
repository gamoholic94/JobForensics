"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { listInvestigations, SavedInvestigation } from "@/lib/api";

function displayClassification(classification: string) {
  if (classification === "Likely Fake") return { label: "fraudulent", tone: "danger" as const };
  if (classification === "Likely Legitimate") return { label: "legitimate", tone: "success" as const };
  return { label: "verification", tone: "warning" as const };
}

function displayDate(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "Unknown date" : date.toLocaleDateString();
}

export function HistoryTable() {
  const [investigations, setInvestigations] = useState<SavedInvestigation[]>([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    listInvestigations()
      .then((items) => {
        if (active) setInvestigations(items);
      })
      .catch((requestError) => {
        if (active) setError(requestError instanceof Error ? requestError.message : "Could not load investigation history.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const filtered = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (!normalized) return investigations;
    return investigations.filter((item) =>
      [item.title, item.company, item.classification, item.source_url]
        .join(" ")
        .toLowerCase()
        .includes(normalized),
    );
  }, [investigations, query]);

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-semibold text-[#315fce]">Records</p>
        <h1 className="mt-1 text-3xl font-bold">Analysis History</h1>
        <p className="mt-2 text-sm text-[var(--muted)]">Review previously saved job investigations.</p>
      </div>
      <Card className="overflow-hidden">
        <div className="border-b border-[var(--border)] p-4">
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            className="w-full max-w-md rounded-xl border border-[var(--border)] bg-transparent px-3 py-2.5 text-sm outline-none"
            placeholder="Search history..."
            aria-label="Search investigation history"
          />
        </div>
        {loading && <p className="p-6 text-sm text-[var(--muted)]">Loading investigations...</p>}
        {!loading && error && <p className="p-6 text-sm text-red-600" role="alert">{error}</p>}
        {!loading && !error && filtered.length === 0 && (
          <div className="p-8 text-center text-sm text-[var(--muted)]">
            {investigations.length === 0
              ? <>No saved investigations yet. <Link href="/detect" className="font-semibold text-[#315fce]">Analyze a job</Link> to create one.</>
              : "No investigations match your search."}
          </div>
        )}
        {!loading && !error && filtered.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[760px] text-left text-sm">
              <thead className="bg-black/[.025] text-xs text-[var(--muted)] dark:bg-white/[.03]">
                <tr>{["Job", "Company", "Result", "Risk", "Date"].map((heading) => <th key={heading} className="px-5 py-3 font-semibold">{heading}</th>)}</tr>
              </thead>
              <tbody>
                {filtered.map((item) => {
                  const classification = displayClassification(item.classification);
                  return (
                    <tr key={item.id} className="border-t border-[var(--border)]">
                      <td className="px-5 py-4 font-medium">
                        <Link href={`/investigations/${item.id}`} className="hover:text-[#315fce]">{item.title || "Job posting"}</Link>
                      </td>
                      <td className="px-5 py-4 text-[var(--muted)]">{item.company || "Unavailable"}</td>
                      <td className="px-5 py-4"><Badge tone={classification.tone}>{classification.label}</Badge></td>
                      <td className="px-5 py-4 font-semibold">{item.overall_risk_score == null ? "Unavailable" : `${Math.round(item.overall_risk_score)}/100`}</td>
                      <td className="px-5 py-4 text-[var(--muted)]">{displayDate(item.created_at)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
