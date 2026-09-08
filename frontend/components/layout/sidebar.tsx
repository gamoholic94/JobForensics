 "use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard, Search, Upload, BriefcaseBusiness, History,
  BarChart3, BookOpen, Settings, ShieldCheck, Menu, X
} from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";

const nav = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/detect", label: "Detect Job Posting", icon: Search },
  { href: "/detect", label: "Upload & Analyze", icon: Upload },
  { href: "/listings", label: "Job Listings", icon: BriefcaseBusiness },
  { href: "/history", label: "History", icon: History },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/guide", label: "Guide", icon: BookOpen },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="fixed left-4 top-4 z-50 rounded-xl border border-[var(--border)] bg-[var(--card)] p-2 shadow-sm lg:hidden"
        aria-label="Open navigation"
      >
        <Menu size={20} />
      </button>

      {open && <div className="fixed inset-0 z-40 bg-black/40 lg:hidden" onClick={() => setOpen(false)} />}

      <aside className={cn(
        "fixed inset-y-0 left-0 z-50 flex w-[260px] flex-col border-r border-[var(--border)] bg-[#101a2d] px-4 py-5 text-white transition-transform lg:translate-x-0",
        open ? "translate-x-0" : "-translate-x-full"
      )}>
        <div className="flex items-center justify-between px-2">
          <Link href="/dashboard" onClick={() => setOpen(false)} className="flex items-center gap-3">
            <div className="grid size-10 place-items-center rounded-xl bg-[#315fce] shadow-lg">
              <ShieldCheck size={24} />
            </div>
            <div>
              <div className="text-xl font-bold tracking-tight">JobForensics</div>
              <div className="text-[11px] text-slate-300">Safer Jobs. Brighter Futures.</div>
            </div>
          </Link>
          <button className="lg:hidden" onClick={() => setOpen(false)}><X size={20} /></button>
        </div>

        <nav className="mt-8 space-y-1.5">
          {nav.map(({ href, label, icon: Icon }) => {
            const active = pathname === href || (href !== "/dashboard" && pathname.startsWith(href));
            return (
              <Link
                key={label}
                href={href}
                onClick={() => setOpen(false)}
                className={cn(
                  "flex items-center gap-3 rounded-xl px-3 py-3 text-sm font-medium transition",
                  active ? "bg-[#315fce] text-white shadow-md" : "text-slate-300 hover:bg-white/10 hover:text-white"
                )}
              >
                <Icon size={18} />
                {label}
              </Link>
            );
          })}
        </nav>

        <div className="mt-auto">
          <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
            <div className="flex items-center gap-2 font-semibold"><ShieldCheck size={18} /> Stay Safe!</div>
            <p className="mt-2 text-xs leading-5 text-slate-300">Always verify before you apply. We help you avoid job scams.</p>
          </div>
          <div className="mt-4 px-2 text-xs text-slate-400">JobForensics v1.0<br />Built for safer careers.</div>
        </div>
      </aside>
    </>
  );
}
