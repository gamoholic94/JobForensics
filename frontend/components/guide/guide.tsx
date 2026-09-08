import { Card } from "@/components/ui/card";
import { ShieldCheck, Search, CreditCard, Building2 } from "lucide-react";

const tips = [
  [Search, "Check the application channel", "Prefer an official company careers page or a verified hiring platform. Be cautious of shortened or unusual domains."],
  [Building2, "Verify the employer", "Look for a real company website, address, employees, and consistent contact information."],
  [CreditCard, "Never pay to get a job", "Registration, training, equipment, or interview fees are major warning signs."],
  [ShieldCheck, "Protect personal information", "Do not share banking credentials, OTPs, passwords, or unnecessary identity documents during early screening."],
];

export function Guide() {
  return <div className="mx-auto max-w-5xl space-y-6">
    <div><p className="text-sm font-semibold text-[#315fce]">Safety Center</p><h1 className="mt-1 text-3xl font-bold">Job Scam Safety Guide</h1><p className="mt-2 text-sm text-[var(--muted)]">Use these checks alongside JobForensics' model prediction.</p></div>
      <div><p className="text-sm font-semibold text-[#315fce]">Safety Center</p><h1 className="mt-1 text-3xl font-bold">Job Scam Safety Guide</h1><p className="mt-2 text-sm text-[var(--muted)]">Use these checks alongside JobForensics' model prediction.</p></div>
    <div className="grid gap-4 md:grid-cols-2">{tips.map(([Icon, title, text]) => { const I = Icon as typeof ShieldCheck; return <Card key={title as string} className="p-6"><div className="grid size-11 place-items-center rounded-xl bg-[#eaf0ff] text-[#315fce]"><I size={21} /></div><h2 className="mt-5 font-bold">{title as string}</h2><p className="mt-2 text-sm leading-6 text-[var(--muted)]">{text as string}</p></Card>})}</div>
    <Card className="border-amber-200 bg-amber-50 p-6 dark:bg-amber-950/20"><h2 className="font-bold text-amber-800 dark:text-amber-300">Important</h2><p className="mt-2 text-sm leading-6 text-amber-700 dark:text-amber-300">A model prediction is an assistive signal, not proof that a job is fraudulent or legitimate. Always verify independently.</p></Card>
  </div>;
}
