import { Card } from "@/components/ui/card";

export function RedFlags({ flags }: { flags: Array<{ name: string; percentage: number }> }) {
  return (
    <Card className="p-5">
      <h2 className="text-lg font-bold">Common Red Flags</h2>
      <p className="text-sm text-[var(--muted)]">Indicators found in saved investigations.</p>
      {flags.length === 0 ? (
        <p className="mt-6 text-sm text-[var(--muted)]">Saved rule evidence will appear here after investigations are stored.</p>
      ) : (
        <div className="mt-6 space-y-5">
          {flags.map((flag) => (
            <div key={flag.name}>
              <div className="mb-2 flex justify-between gap-3 text-sm">
                <span>{flag.name}</span><span className="font-bold text-red-600">{flag.percentage}%</span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
                <div className="h-full rounded-full bg-red-500" style={{ width: `${flag.percentage}%` }} />
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}
