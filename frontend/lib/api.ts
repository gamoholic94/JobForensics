export type Prediction = {
  success: boolean;
  classification: "Likely Fake" | "Likely Legitimate" | "Needs Review";
  prediction: "legitimate" | "fraudulent" | "verification";
  probability: number;
  confidence: number;
  reasons: string[];
  model_probability: {
    fake_probability: number;
    label: "Fake" | "Real";
  };
  risk: {
    overall_risk_score: number;
    risk_level: string;
    component_scores: Record<string, number>;
  };
  recommendations: string[];
  job: {
    title: string;
    company: string;
    location: string;
    employment_type: string;
  };
  domain_analysis: Record<string, unknown>;
  company_analysis: Record<string, unknown>;
  salary_analysis: Record<string, unknown>;
  application_analysis: Record<string, unknown>;
  content_risk: { rules: Array<Record<string, unknown>> };
  explanations?: Record<string, unknown>;
};

export type BatchPredictionItem = {
  row: number;
  url: string;
  result?: Prediction;
  error?: string;
};

export type BatchPrediction = {
  success: boolean;
  total: number;
  completed: number;
  failed: number;
  results: BatchPredictionItem[];
};

export async function analyzeJob(payload: Record<string, unknown>): Promise<Prediction> {
  const response = await fetch("/api/predict", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    let message = `Prediction API failed: ${response.status}`;
    try {
      const errorBody = await response.json();
      message = errorBody.detail || errorBody.error || message;
    } catch {
      // Keep the status message when the service returns a non-JSON error.
    }
    throw new Error(message);
  }

  const result = await response.json();
  const classification = result.classification as Prediction["classification"];
  const probability = Number(result.model_probability?.fake_probability ?? 0);

  return {
    ...result,
    prediction: classification === "Likely Fake"
      ? "fraudulent"
      : classification === "Likely Legitimate" ? "legitimate" : "verification",
    probability,
    confidence: probability,
    reasons: result.recommendations || [],
  } as Prediction;
}

export async function analyzeBatch(payload: Record<string, unknown>): Promise<BatchPrediction> {
  const response = await fetch("/api/predict/batch", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    let message = `Batch prediction API failed: ${response.status}`;
    try {
      const errorBody = await response.json();
      message = errorBody.detail || errorBody.error || message;
    } catch {
      // Keep the status message when the service returns a non-JSON error.
    }
    throw new Error(message);
  }

  return response.json() as Promise<BatchPrediction>;
}
