 "use client";

import { Bell, Search } from "lucide-react";
import { ThemeToggle } from "./theme-toggle";

export function Header() {
  return (
    <header className="sticky top-0 z-30 flex h-[72px] items-center gap-4 border-b border-[var(--border)] bg-[var(--background)]/90 px-5 backdrop-blur lg:px-8">
      <div className="ml-12 flex min-w-0 flex-1 items-center gap-3 lg:ml-0">
        <div className="hidden w-full max-w-md items-center gap-2 rounded-xl border border-[var(--border)] bg-[var(--card)] px-3 py-2.5 sm:flex">
          <Search size={17} className="text-[var(--muted)]" />
          <input className="w-full bg-transparent text-sm outline-none" placeholder="Search jobs, keywords, or companies..." />
        </div>
      </div>
      <ThemeToggle />
      <button className="rounded-xl p-2.5 hover:bg-black/[.04] dark:hover:bg-white/[.05]" aria-label="Notifications">
        <Bell size={19} />
      </button>
      <div className="grid size-9 place-items-center rounded-full bg-[#15294b] text-sm font-bold text-white">JF</div>
    </header>
  );
}
