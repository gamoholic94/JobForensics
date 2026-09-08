# JobForensics Frontend

Production-oriented Next.js frontend boilerplate for an AI-powered fraud job detection application.

## Stack

- Next.js + TypeScript
- Tailwind CSS
- Recharts
- React Hook Form / Zod ready
- Framer Motion
- Lucide icons
- next-themes

## Routes

- `/dashboard`
- `/detect`
- `/result`
- `/listings`
- `/history`
- `/analytics`
- `/guide`
- `/settings`

## Local setup

```bash
npm install
npm run dev
```

Open `http://localhost:3000`.

## Connect the ML API

Create `.env.local`:

```env
BACKEND_API_URL=http://localhost:8000
```

The browser calls the same-origin Next route `/api/predict`. That route forwards
requests to the server-only `BACKEND_API_URL`, so the Python service URL and any
future credentials are not exposed to the browser.

The Python service accepts:

```text
POST /predict
```

The request accepts `url` (including Google Forms links), `description`, or a
base64-encoded `file_name` and `file_content_base64` pair for PDF/TXT uploads,
plus optional `title`, `company_name`, `location`, and `employment_type` fields.
The response is the unified result from the Python pipeline.

## Vercel deployment

1. Deploy the Python service from the repository root with `uvicorn api_server:app --host 0.0.0.0 --port $PORT`.
2. Make sure the Python service has `models/model.pkl`; run `python -m src.model` first if needed.
3. Import `jobguard-frontend-boilerplate` into Vercel as the Root Directory.
4. Set `BACKEND_API_URL` to the deployed Python service URL in Vercel Environment Variables.
5. Deploy the Next.js app.

The Vercel proxy means browser CORS is not required. Direct browser clients can
use `ALLOWED_ORIGINS` on the Python service if they are added later.

## Important production work

Before public launch:
- Add authentication if user-specific history is required.
- Add server-side validation and rate limiting.
- Never expose secret API keys with `NEXT_PUBLIC_`.
- Configure backend CORS.
- Replace dashboard mock data with real API/database data.
- Add proper loading/error/empty states.
- Add model/version metadata to predictions.
