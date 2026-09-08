 "use client";

import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export function Settings() {
  const [saved, setSaved] = useState(false);
  return <div className="mx-auto max-w-3xl space-y-6">
    <div><p className="text-sm font-semibold text-[#315fce]">Preferences</p><h1 className="mt-1 text-3xl font-bold">Settings</h1><p className="mt-2 text-sm text-[var(--muted)]">Configure your JobForensics experience.</p></div>
      <div><p className="text-sm font-semibold text-[#315fce]">Preferences</p><h1 className="mt-1 text-3xl font-bold">Settings</h1><p className="mt-2 text-sm text-[var(--muted)]">Configure your JobForensics experience.</p></div>
    <Card className="p-6 space-y-6">
      <div><div className="font-semibold">API connection</div><p className="mt-1 text-sm text-[var(--muted)]">Set BACKEND_API_URL in your Vercel project environment variables.</p></div>
      <div><div className="font-semibold">Notifications</div><label className="mt-3 flex items-center justify-between rounded-xl border border-[var(--border)] p-4 text-sm"><span>Fraud alert notifications</span><input type="checkbox" defaultChecked /></label></div>
      <div><div className="font-semibold">Privacy</div><p className="mt-1 text-sm text-[var(--muted)]">Do not send sensitive personal information to the prediction endpoint.</p></div>
      <Button onClick={() => setSaved(true)}>{saved ? "Saved" : "Save preferences"}</Button>
    </Card>
  </div>;
}
