 "use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Link2, FileText, UploadCloud, FileSpreadsheet, ShieldCheck, Loader2 } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { analyzeBatch, analyzeJob } from "@/lib/api";

export function JobScanner() {
  const router = useRouter();
  const [mode, setMode] = useState<"url" | "text" | "file" | "csv">("url");
  const [url, setUrl] = useState("");
  const [title, setTitle] = useState("");
  const [company, setCompany] = useState("");
  const [description, setDescription] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function fileAsBase64(selectedFile: File) {
    const bytes = new Uint8Array(await selectedFile.arrayBuffer());
    let binary = "";
    const chunkSize = 0x8000;
    for (let index = 0; index < bytes.length; index += chunkSize) {
      binary += String.fromCharCode(...bytes.subarray(index, index + chunkSize));
    }
    return btoa(binary);
  }

  async function submit() {
    setError("");

    if (mode === "url") {
      try {
        const parsedUrl = new URL(url.trim());
        if (!(["http:", "https:"].includes(parsedUrl.protocol) && parsedUrl.hostname)) {
          throw new Error();
        }
      } catch {
        setError("Please enter a valid job posting URL, including https://.");
        return;
      }
    }

    if (mode === "file" && file && file.size > 3_000_000) {
      setError("Please upload a PDF or TXT file smaller than 3 MB.");
      return;
    }

    if (mode === "csv" && csvFile && csvFile.size > 3_000_000) {
      setError("Please upload a CSV smaller than 3 MB.");
      return;
    }

    setLoading(true);
    try {
      let payload: Record<string, unknown>;
      if (mode === "csv" && csvFile) {
        const result = await analyzeBatch({ file_name: csvFile.name, file_content_base64: await fileAsBase64(csvFile) });
        sessionStorage.setItem("jobforensics-batch-result", JSON.stringify(result));
        router.push("/batch-result");
        return;
      } else if (mode === "url") {
        payload = { url: url.trim() };
      } else if (mode === "file" && file) {
        payload = { file_name: file.name, file_content_base64: await fileAsBase64(file) };
      } else {
        payload = { title, company_name: company, description };
      }

      const result = await analyzeJob(payload);
      sessionStorage.setItem("jobforensics-result", JSON.stringify(result));
      router.push("/result");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Analysis failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  const scannerModes = [
    ["url", "Job URL", Link2],
    ["text", "Description", FileText],
    ["file", "Upload", UploadCloud],
    ["csv", "Batch CSV", FileSpreadsheet],
  ] as const;

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <p className="text-sm font-semibold text-[#315fce]">AI Scanner</p>
        <h1 className="mt-1 text-3xl font-bold tracking-tight">Check a Job Before You Apply</h1>
        <p className="mt-2 text-sm text-[var(--muted)]">Paste a job URL, enter the description, or upload a job file.</p>
      </div>

      <Card className="overflow-hidden">
        <div className="flex border-b border-[var(--border)]">
          {scannerModes.map(([key, label, Icon]) => (
            <button key={key} onClick={() => setMode(key as typeof mode)} className={`flex flex-1 items-center justify-center gap-2 px-3 py-4 text-sm font-semibold ${mode === key ? "border-b-2 border-[#315fce] text-[#315fce]" : "text-[var(--muted)]"}`}>
              <Icon size={17} /> {label}
            </button>
          ))}
        </div>

        <div className="p-6 lg:p-8">
          {mode === "url" && (
            <div>
              <label className="text-sm font-semibold">Job posting or Google Forms URL</label>
              <div className="mt-2 flex flex-col gap-3 sm:flex-row">
                <div className="flex flex-1 items-center gap-2 rounded-xl border border-[var(--border)] px-3">
                  <Link2 size={18} className="text-[var(--muted)]" />
                  <input value={url} onChange={e => setUrl(e.target.value)} className="w-full bg-transparent py-3 outline-none" placeholder="https://example.com/job-posting" aria-invalid={Boolean(error)} />
                </div>
                <Button onClick={submit} disabled={!url || loading}>{loading ? <Loader2 className="animate-spin" size={17} /> : null} Analyze Job</Button>
              </div>
              <p className="mt-2 text-xs text-[var(--muted)]">Job portals that block automated access return a limited result. Paste the description for a fuller analysis.</p>
            </div>
          )}

          {mode === "text" && (
            <div className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <label className="text-sm font-semibold">Job title<input value={title} onChange={e => setTitle(e.target.value)} className="mt-2 w-full rounded-xl border border-[var(--border)] bg-transparent px-3 py-3 outline-none" placeholder="Software Developer Intern" /></label>
                <label className="text-sm font-semibold">Company<input value={company} onChange={e => setCompany(e.target.value)} className="mt-2 w-full rounded-xl border border-[var(--border)] bg-transparent px-3 py-3 outline-none" placeholder="Example Technologies" /></label>
              </div>
              <label className="block text-sm font-semibold">Job description<textarea value={description} onChange={e => setDescription(e.target.value)} rows={9} className="mt-2 w-full resize-none rounded-xl border border-[var(--border)] bg-transparent px-3 py-3 outline-none" placeholder="Paste the complete job description here..." /></label>
              <Button onClick={submit} disabled={!description || loading}>{loading ? <Loader2 className="animate-spin" size={17} /> : null} Analyze Job</Button>
            </div>
          )}

          {mode === "file" && (
            <div>
              <label className="flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed border-[var(--border)] p-10 text-center hover:border-[#315fce]">
                <UploadCloud size={35} className="text-[#315fce]" />
                <span className="mt-3 font-semibold">{file ? file.name : "Drop a job file here"}</span>
                <span className="mt-1 text-xs text-[var(--muted)]">PDF or TXT</span>
                <input type="file" accept=".pdf,.txt" className="hidden" onChange={e => setFile(e.target.files?.[0] || null)} />
              </label>
              <div className="mt-4"><Button onClick={submit} disabled={!file || loading}>{loading ? <Loader2 className="animate-spin" size={17} /> : null} Analyze File</Button></div>
            </div>
          )}

          {mode === "csv" && (
            <div>
              <label className="flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed border-[var(--border)] p-10 text-center hover:border-[#315fce]">
                <FileSpreadsheet size={35} className="text-[#315fce]" />
                <span className="mt-3 font-semibold">{csvFile ? csvFile.name : "Upload a CSV of job links"}</span>
                <span className="mt-1 text-xs text-[var(--muted)]">Use a url, link, or job_url column. Up to 50 links.</span>
                <input type="file" accept=".csv,text/csv" className="hidden" onChange={e => setCsvFile(e.target.files?.[0] || null)} />
              </label>
              <div className="mt-4"><Button onClick={submit} disabled={!csvFile || loading}>{loading ? <Loader2 className="animate-spin" size={17} /> : null} Analyze CSV</Button></div>
            </div>
          )}

          {error && <p className="mt-4 text-sm text-red-600" role="alert">{error}</p>}

          <div className="mt-7 flex items-center gap-2 text-xs text-[var(--muted)]">
            <ShieldCheck size={15} className="text-emerald-600" /> Your analysis is designed to help you verify opportunities before applying.
          </div>
        </div>
      </Card>
    </div>
  );
}
