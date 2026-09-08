import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Search } from "lucide-react";

const jobs = [
  ["Frontend Developer", "TechNova", "Software Development", "legitimate", "91%"],
  ["Data Entry Operator", "Quick Earners", "Operations", "fraudulent", "95%"],
  ["ML Engineer", "AI Labs", "Data Science", "legitimate", "97%"],
  ["Work From Home Agent", "Fast Money Ltd", "Customer Support", "fraudulent", "93%"],
  ["Product Analyst", "Bright Minds", "Data Science", "verification", "61%"],
];

export function JobListings() {
  return <div className="space-y-6">
    <div><p className="text-sm font-semibold text-[#315fce]">Explore</p><h1 className="mt-1 text-3xl font-bold">Job Listings</h1><p className="mt-2 text-sm text-[var(--muted)]">Browse analyzed opportunities and their risk assessments.</p></div>
    <Card className="p-4"><div className="flex flex-col gap-3 md:flex-row"><div className="flex flex-1 items-center gap-2 rounded-xl border border-[var(--border)] px-3"><Search size={17} className="text-[var(--muted)]" /><input className="w-full bg-transparent py-2.5 text-sm outline-none" placeholder="Search job title or company..." /></div><select className="rounded-xl border border-[var(--border)] bg-transparent px-3 py-2.5 text-sm"><option>All results</option><option>Legitimate</option><option>Fraudulent</option><option>Verification</option></select></div></Card>
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{jobs.map(j => <Card key={j[0]} className="p-5"><div className="flex items-start justify-between gap-3"><div><h2 className="font-bold">{j[0]}</h2><p className="mt-1 text-sm text-[var(--muted)]">{j[1]}</p></div><Badge tone={j[3] === "fraudulent" ? "danger" : j[3] === "legitimate" ? "success" : "warning"}>{j[3]}</Badge></div><div className="mt-5 text-xs text-[var(--muted)]">{j[2]}</div><div className="mt-3 flex items-center justify-between"><span className="text-sm">Confidence</span><span className="font-bold">{j[4]}</span></div></Card>)}</div>
  </div>;
}
