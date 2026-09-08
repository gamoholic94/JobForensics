 "use client";

import { motion } from "framer-motion";
import { AlertTriangle, BriefcaseBusiness, Building2, CheckCircle2, ArrowUpRight, ShieldCheck } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { TrendChart } from "./trend-chart";
import { JobDistribution } from "./job-distribution";
import { RecentPredictions } from "./recent-predictions";
import { RedFlags } from "./red-flags";
import Link from "next/link";

const stats = [
  { label: "Total Job Postings", value: "12,486", meta: "+12%", note: "Analyzed so far", icon: BriefcaseBusiness, tone: "blue" },
  { label: "Legitimate Jobs", value: "9,842", meta: "78.9%", note: "Likely genuine opportunities", icon: CheckCircle2, tone: "green" },
  { label: "Fraudulent Jobs", value: "2,644", meta: "21.1%", note: "Potential scams detected", icon: AlertTriangle, tone: "red" },
  { label: "Companies", value: "1,327", meta: "+8%", note: "Unique companies analyzed", icon: Building2, tone: "purple" },
];

export function Dashboard() {
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
                <div className="mt-5 text-2xl font-bold">{s.value}</div>
                <div className="mt-1 text-sm font-medium">{s.label}</div>
                <div className="mt-1 text-xs text-[var(--muted)]">{s.note}</div>
              </Card>
            </motion.div>
          );
        })}
      </div>

      <div className="grid gap-5 xl:grid-cols-[1.55fr_1fr]">
        <TrendChart />
        <JobDistribution />
      </div>

      <div className="grid gap-5 xl:grid-cols-[1.55fr_1fr]">
        <RecentPredictions />
        <RedFlags />
      </div>

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
