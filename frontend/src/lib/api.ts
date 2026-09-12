const CANDIDATE_URLS = [
  process.env.NEXT_PUBLIC_API_URL,
  'http://localhost:8000/api/v1',
  'http://localhost:8001/api/v1',
].filter(Boolean) as string[];

let resolvedBaseUrl: string | null = null;

async function getBaseUrl(): Promise<string> {
  if (resolvedBaseUrl) return resolvedBaseUrl;
  for (const url of CANDIDATE_URLS) {
    const root = url.replace(/\/api\/v1\/?$/, '');
    try {
      const res = await fetch(`${root}/health`, { signal: AbortSignal.timeout(800) });
      if (res.ok) {
        const data = await res.json();
        if (data.legal_entities) {
          resolvedBaseUrl = url;
          return url;
        }
      }
    } catch {}
  }
  return 'http://localhost:8001/api/v1';
}

export async function fetchHITLQueue(entityCode: string) {
  const baseUrl = await getBaseUrl();
  const res = await fetch(`${baseUrl}/hitl/queue/${entityCode}`, { cache: 'no-store' });
  if (!res.ok) throw new Error(`Failed to fetch HITL queue: ${res.statusText}`);
  return res.json();
}

export async function submitHITLDecision(payload: {
  draft_action_id: string;
  operator_id: string;
  decision: 'APPROVE' | 'EDIT' | 'DISCARD';
  modified_narrative?: string;
}) {
  const baseUrl = await getBaseUrl();
  const res = await fetch(`${baseUrl}/hitl/decision`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`Decision submission failed: ${res.statusText}`);
  return res.json();
}