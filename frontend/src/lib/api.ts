export function getCandidateRoots(): string[] {
  const roots: string[] = [];
  if (process.env.NEXT_PUBLIC_API_URL) {
    roots.push(process.env.NEXT_PUBLIC_API_URL.replace(/\/api\/v1\/?$/, ''));
  }
  if (typeof window !== 'undefined' && window.location?.hostname) {
    roots.push(`http://${window.location.hostname}:8000`);
    roots.push(`http://${window.location.hostname}:8001`);
  }
  roots.push('http://localhost:8000');
  roots.push('http://localhost:8001');
  return Array.from(new Set(roots.filter(Boolean)));
}

let resolvedRoot: string | null = null;
let resolvedBaseUrl: string | null = null;

export async function getApiRoot(): Promise<string> {
  if (resolvedRoot) return resolvedRoot;
  const candidates = getCandidateRoots();
  for (const root of candidates) {
    try {
      const res = await fetch(`${root}/health`, { signal: AbortSignal.timeout(1000) });
      if (res.ok) {
        const data = await res.json();
        if (data.legal_entities) {
          resolvedRoot = root;
          resolvedBaseUrl = `${root}/api/v1`;
          return root;
        }
      }
    } catch {}
  }
  const fallback = typeof window !== 'undefined' && window.location?.hostname
    ? `http://${window.location.hostname}:8000`
    : 'http://localhost:8000';
  resolvedRoot = fallback;
  resolvedBaseUrl = `${fallback}/api/v1`;
  return fallback;
}

export async function getBaseUrl(): Promise<string> {
  if (resolvedBaseUrl) return resolvedBaseUrl;
  await getApiRoot();
  return resolvedBaseUrl || 'http://localhost:8000/api/v1';
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