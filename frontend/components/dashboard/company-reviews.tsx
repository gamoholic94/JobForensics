"use client";

import { useState } from "react";
import { ExternalLink, Search, ShieldAlert } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

type Review = {
  id: string; title: string; text: string; source: string; subreddit: string;
  author: string; score: number; url: string; status: string; status_explanation: string;
};

export function CompanyReviews() {
  const [company, setCompany] = useState("");
  const [reviews, setReviews] = useState<Review[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function search() {
    setError("");
    setLoading(true);
    try {
      const response = await fetch(`/api/public-reviews?company=${encodeURIComponent(company)}`);
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail || body.error || "Could not load reviews.");
      setReviews(body.reviews);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Could not load reviews.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card className="p-5">
      <div className="flex items-start gap-3">
        <div className="grid size-10 place-items-center rounded-xl bg-amber-50 text-amber-600"><ShieldAlert size={20} /></div>
        <div><h2 className="font-bold">Public company reviews</h2><p className="text-sm text-[var(--muted)]">Search public Reddit discussions. Statuses are signals, not proof.</p></div>
      </div>
      <div className="mt-4 flex gap-2">
        <input value={company} onChange={(event) => setCompany(event.target.value)} onKeyDown={(event) => event.key === "Enter" && search()} placeholder="Company name" className="min-w-0 flex-1 rounded-xl border border-[var(--border)] bg-transparent px-3 py-2.5 outline-none" />
        <Button onClick={search} disabled={loading || company.trim().length < 2}><Search size={16} /> {loading ? "Searching..." : "Search"}</Button>
      </div>
      {error && <p className="mt-3 text-sm text-red-600" role="alert">{error}</p>}
      <div className="mt-5 space-y-3">
        {reviews.map((review) => (
          <div key={review.id} className="rounded-xl border border-[var(--border)] p-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="font-semibold">{review.title}</div>
              <span className={`rounded-full px-2 py-1 text-xs font-bold ${review.status === "Suspicious" ? "bg-red-100 text-red-700" : review.status === "Likely authentic" ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700"}`}>{review.status}</span>
            </div>
            <p className="mt-2 line-clamp-3 text-sm text-[var(--muted)]">{review.text}</p>
            <div className="mt-3 flex flex-wrap items-center gap-3 text-xs text-[var(--muted)]">
              <span>{review.subreddit || "Reddit"} · {review.score} points</span>
              {review.url && <a href={review.url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-[#315fce]">Open source <ExternalLink size={13} /></a>}
            </div>
            <p className="mt-2 text-xs text-[var(--muted)]">{review.status_explanation}</p>
          </div>
        ))}
        {!loading && company && reviews.length === 0 && !error && <p className="text-sm text-[var(--muted)]">No matching public Reddit discussions were found.</p>}
      </div>
    </Card>
  );
}
