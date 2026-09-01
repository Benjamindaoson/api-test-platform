
/**
 * Management API client — talks to the FastAPI backend.
 *
 * The agent server and the management API are separate
 * services. This client lets the UI trigger platform operations such as code
 * analysis, test execution and endpoint synchronisation directly, while the
 * chat agent uses the same operations through its tools.
 */

const MANAGEMENT_API_URL =
  process.env.NEXT_PUBLIC_MANAGEMENT_API_URL ?? "http://localhost:8100";

function getUrl(path: string): string {
  const base = MANAGEMENT_API_URL.replace(/\/$/, "");
  return `${base}${path}`;
}

async function fetchJson(
  path: string,
  options?: RequestInit,
): Promise<unknown> {
  const res = await fetch(getUrl(path), {
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers || {}),
    },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Management API error ${res.status}: ${text}`);
  }
  return res.json();
}

export interface AnalyzeRequest {
  project_id?: string;
  project_path?: string;
  base_branch?: string;
}

export interface TestRequest {
  project_id?: string;
  test_path?: string;
  marker?: string;
  parallel?: number;
}

export interface EndpointSyncRequest {
  project_id: string;
}

export interface ProjectCreateRequest {
  name: string;
  repo_url?: string;
  openapi_spec?: string;
  base_url?: string;
  description?: string;
}

export async function analyzeCode(body: AnalyzeRequest): Promise<unknown> {
  return fetchJson("/api/analyze", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function runTests(body: TestRequest): Promise<unknown> {
  return fetchJson("/api/test", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function listEndpoints(projectId?: string): Promise<unknown[]> {
  const qs = projectId ? `?project_id=${encodeURIComponent(projectId)}` : "";
  return fetchJson(`/api/endpoints${qs}`) as Promise<unknown[]>;
}

export async function syncEndpoints(
  body: EndpointSyncRequest,
): Promise<unknown> {
  return fetchJson("/api/endpoints/sync", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function listProjects(): Promise<unknown[]> {
  return fetchJson("/api/projects") as Promise<unknown[]>;
}

export async function getProject(id: string): Promise<unknown> {
  return fetchJson(`/api/projects/${id}`);
}

export async function createProject(body: ProjectCreateRequest): Promise<unknown> {
  return fetchJson("/api/projects", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function listRuns(projectId?: string): Promise<unknown[]> {
  const qs = projectId ? `?project_id=${encodeURIComponent(projectId)}` : "";
  return fetchJson(`/api/runs${qs}`) as Promise<unknown[]>;
}

export async function listReports(
  projectId?: string,
  reportType?: string,
): Promise<unknown[]> {
  const params = new URLSearchParams();
  if (projectId) params.set("project_id", projectId);
  if (reportType) params.set("report_type", reportType);
  const qs = params.toString() ? `?${params.toString()}` : "";
  return fetchJson(`/api/reports${qs}`) as Promise<unknown[]>;
}
