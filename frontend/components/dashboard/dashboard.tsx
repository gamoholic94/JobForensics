 "use client";

 import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { AlertTriangle, BriefcaseBusiness, Building2, CheckCircle2, ArrowUpRight, ShieldCheck } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { TrendChart } from "./trend-chart";
import { JobDistribution } from "./job-distribution";
import { RecentPredictions } from "./recent-predictions";
import { RedFlags } from "./red-flags";
import { CompanyReviews } from "./company-reviews";
import Link from "next/link";
import { getInvestigationStats, listInvestigations, SavedInvestigation } from "@/lib/api";

export function Dashboard() {
  const [investigations, setInvestigations] = useState<SavedInvestigation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [redFlags, setRedFlags] = useState<Array<{ name: string; percentage: number }>>([]);

  useEffect(() => {
    Promise.all([listInvestigations(), getInvestigationStats()])
      .then(([items, stats]) => {
        setInvestigations(items);
        setRedFlags(stats.red_flags);
      })
      .catch((requestError) => setError(requestError instanceof Error ? requestError.message : "Could not load dashboard data."))
      .finally(() => setLoading(false));
  }, []);

  const stats = useMemo(() => {
    const legitimate = investigations.filter((item) => item.classification === "Likely Legitimate").length;
    const fraudulent = investigations.filter((item) => item.classification === "Likely Fake").length;
    const companies = new Set(investigations.map((item) => item.company).filter(Boolean)).size;
    return [
      { label: "Saved Investigations", value: investigations.length, meta: "", note: "Persisted analysis records", icon: BriefcaseBusiness, tone: "blue" },
      { label: "Likely Legitimate", value: legitimate, meta: investigations.length ? `${Math.round((legitimate / investigations.length) * 100)}%` : "", note: "Current saved records", icon: CheckCircle2, tone: "green" },
      { label: "Likely Fraudulent", value: fraudulent, meta: investigations.length ? `${Math.round((fraudulent / investigations.length) * 100)}%` : "", note: "Potential scams detected", icon: AlertTriangle, tone: "red" },
      { label: "Companies", value: companies, meta: "", note: "Unique saved companies", icon: Building2, tone: "purple" },
    ];
  }, [investigations]);

  const trendData = useMemo(() => {
    const grouped = new Map<string, { legit: number; fraud: number }>();
    for (const item of investigations) {
      const day = new Date(item.created_at).toLocaleDateString(undefined, { month: "short", day: "numeric" });
      const entry = grouped.get(day) || { legit: 0, fraud: 0 };
      if (item.classification === "Likely Fake") entry.fraud += 1;
      else if (item.classification === "Likely Legitimate") entry.legit += 1;
      grouped.set(day, entry);
    }
    return Array.from(grouped, ([day, values]) => ({ day, ...values })).reverse();
  }, [investigations]);

  const distribution = [
    { name: "Likely Legitimate", value: stats[1].value, color: "#12b76a" },
    { name: "Likely Fraudulent", value: stats[2].value, color: "#f04438" },
    { name: "Needs Review", value: investigations.filter((item) => item.classification === "Needs Review").length, color: "#f79009" },
  ];

  return (
    <div className="space-y-7">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm font-semibold text-[#315fce]">Overview</p>
          <h1 className="mt-1 text-3xl font-bold tracking-tight lg:text-4xl">Fraud Job Detection Dashboard</h1>
          <p className="mt-2 text-sm text-[var(--muted)]">AI-powered analysis to identify fraudulent job postings.</p>
        </div>
        <Link href="/detect" className="inline-flex items-center gap-2 rounded-xl bg-[#315fce] px-4 py-2.5 text-sm font-semibold text-white hover:bg-[#2854ba]">
          Analyze a Job <ArrowUpRight size={17} />
        </Link>
      </div>

      {error && <p className="text-sm text-red-600" role="alert">{error}</p>}
      {loading && <p className="text-sm text-[var(--muted)]">Loading saved investigations...</p>}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {stats.map((s, i) => {
          const Icon = s.icon;
          return (
            <motion.div key={s.label} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * .05 }}>
              <Card className="p-5">
                <div className="flex items-start justify-between">
                  <div className={`grid size-11 place-items-center rounded-xl ${
                    s.tone === "green" ? "bg-emerald-50 text-emerald-600" :
                    s.tone === "red" ? "bg-red-50 text-red-600" :
                    s.tone === "purple" ? "bg-purple-50 text-purple-600" :
                    "bg-blue-50 text-blue-600"
                  }`}>
                    <Icon size={21} />
                  </div>
                  <span className={`text-xs font-bold ${s.tone === "red" ? "text-red-600" : "text-emerald-600"}`}>{s.meta}</span>
                </div>
                <div className="mt-5 text-2xl font-bold">{loading ? "..." : s.value}</div>
                <div className="mt-1 text-sm font-medium">{s.label}</div>
                <div className="mt-1 text-xs text-[var(--muted)]">{s.note}</div>
              </Card>
            </motion.div>
          );
        })}
      </div>

      <div className="grid gap-5 xl:grid-cols-[1.55fr_1fr]">
        <TrendChart data={trendData} />
        <JobDistribution data={distribution} />
      </div>

      <div className="grid gap-5 xl:grid-cols-[1.55fr_1fr]">
        <RecentPredictions investigations={investigations} />
        <RedFlags flags={redFlags} />
      </div>

      <CompanyReviews />

      <Card className="flex flex-col gap-3 p-5 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-3">
          <div className="grid size-10 place-items-center rounded-xl bg-[#eaf0ff] text-[#315fce]"><ShieldCheck size={20} /></div>
          <div>
            <div className="font-semibold">Protect your job search</div>
            <p className="mt-1 text-sm text-[var(--muted)]">Use JobForensics before sharing personal information or paying an employer.</p>
          </div>
        </div>
        <Badge tone="warning">Always verify employers</Badge>
      </Card>
    </div>
  );
}
