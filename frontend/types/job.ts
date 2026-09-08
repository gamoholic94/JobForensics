export type Verdict = "legitimate" | "fraudulent" | "verification";

export type JobRecord = {
  id: string;
  title: string;
  company: string;
  verdict: Verdict;
  confidence: number;
  category: string;
  date: string;
  flags: string[];
};
