"use client";

import { useState } from "react";
import { ExternalLink, ShieldAlert } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

const sources = ["Google", "Glassdoor", "Indeed", "Trustpilot", "LinkedIn", "Other"];

export function CompanyReviews() {
  const [source, setSource] = useState("Google");
  const [url, setUrl] = useState("");
  const [text, setText] = useState("");
  const [review, setReview] = useState<null | { title: string; text: string; source: string; url: string; status: string; status_explanation: string }>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function analyzeReview() {
    setError("");
    setLoading(true);
    try {
      const response = await fetch("/api/public-reviews", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source, url, text }),
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail || body.error || "Could not analyze the review.");
      setReview(body);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Could not analyze the review.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card className="p-5">
      <div className="flex items-start gap-3">
        <div className="grid size-10 place-items-center rounded-xl bg-amber-50 text-amber-600"><ShieldAlert size={20} /></div>
        <div><h2 className="font-bold">Review evidence</h2><p className="text-sm text-[var(--muted)]">Paste a review from a platform. We do not scrape or log in to review websites.</p></div>
      </div>
      <div className="mt-4 grid gap-3 sm:grid-cols-[160px_1fr]">
        <select value={source} onChange={(event) => setSource(event.target.value)} className="rounded-xl border border-[var(--border)] bg-transparent px-3 py-2.5 outline-none">
          {sources.map((item) => <option key={item}>{item}</option>)}
        </select>
        <input value={url} onChange={(event) => setUrl(event.target.value)} placeholder="Optional review link" className="rounded-xl border border-[var(--border)] bg-transparent px-3 py-2.5 outline-none" />
      </div>
      <textarea value={text} onChange={(event) => setText(event.target.value)} rows={5} placeholder="Paste the review text here (at least 20 characters)..." className="mt-3 w-full resize-y rounded-xl border border-[var(--border)] bg-transparent px-3 py-3 outline-none" />
      <Button onClick={analyzeReview} disabled={loading || text.trim().length < 20}>{loading ? "Analyzing..." : "Analyze review"}</Button>
      {error && <p className="mt-3 text-sm text-red-600" role="alert">{error}</p>}
      {review && (
        <div className="mt-5 rounded-xl border border-[var(--border)] p-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="font-semibold">{review.title}</div>
            <span className={`rounded-full px-2 py-1 text-xs font-bold ${review.status === "Suspicious" ? "bg-red-100 text-red-700" : "bg-amber-100 text-amber-700"}`}>{review.status}</span>
          </div>
          <p className="mt-2 text-sm text-[var(--muted)]">{review.text}</p>
          <p className="mt-3 text-xs text-[var(--muted)]">{review.status_explanation}</p>
          {review.url && <a href={review.url} target="_blank" rel="noreferrer" className="mt-3 inline-flex items-center gap-1 text-xs text-[#315fce]">Open source <ExternalLink size={13} /></a>}
        </div>
      )}
    </Card>
  );
}
