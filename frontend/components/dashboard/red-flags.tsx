import { Card } from "@/components/ui/card";

const flags = [
  ["Too-good-to-be-true salary", 68],
  ["No company details", 52],
  ["Requests upfront payment", 47],
  ["Generic job description", 41],
  ["Unrealistic remote offer", 38],
];

export function RedFlags() {
  return (
    <Card className="p-5">
      <h2 className="text-lg font-bold">Common Red Flags</h2>
      <p className="text-sm text-[var(--muted)]">Top indicators found in fraudulent postings.</p>
      <div className="mt-6 space-y-5">
        {flags.map(([name, value]) => (
          <div key={name}>
            <div className="mb-2 flex justify-between gap-3 text-sm">
              <span>{name}</span><span className="font-bold text-red-600">{value}%</span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
              <div className="h-full rounded-full bg-red-500" style={{ width: `${value}%` }} />
            </div>
          </div>
        ))}
      </div>
      <div className="mt-6 rounded-xl bg-red-50 p-3 text-xs leading-5 text-red-700 dark:bg-red-950/30 dark:text-red-300">
        Tip: Be cautious of postings that ask for money, have vague details, or promise high salaries with little effort.
      </div>
    </Card>
  );
}
