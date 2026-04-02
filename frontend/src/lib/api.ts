/**
 * API client functions for the LegacyLens backend.
 */

import type { JobListResponse, JobStatusResponse, JobSummary, DiffResponse } from "./types";

const API_BASE = "/api/v1";

export class AuthError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "AuthError";
  }
}

async function fetchWithAuth(url: string, options: RequestInit = {}) {
  const res = await fetch(url, {
    ...options,
  });
  
  if (res.status === 401) {
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    }
    throw new AuthError("Session expired or unauthorized. Redirecting to login.");
  }
  
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`API failed: ${res.status} ${res.statusText} ${text}`);
  }
  
  return res;
}

export async function submitJob(file: File, dependencies?: File[]): Promise<{ job_id: string; status: string }> {
  const formData = new FormData();
  formData.append("file", file);
  
  if (dependencies) {
    dependencies.forEach((dep) => {
      formData.append("dependencies", dep);
    });
  }

  const res = await fetchWithAuth(`${API_BASE}/jobs`, {
    method: "POST",
    body: formData,
  });

  return res.json();
}

export async function listJobs(page = 1, limit = 20): Promise<JobListResponse> {
  const res = await fetchWithAuth(`${API_BASE}/jobs?page=${page}&limit=${limit}`);
  return res.json();
}

export async function getJobStatus(jobId: string): Promise<JobStatusResponse> {
  const res = await fetchWithAuth(`${API_BASE}/jobs/${jobId}`);
  return res.json();
}

export async function getArtifact(jobId: string, name: string): Promise<string> {
  const res = await fetchWithAuth(`${API_BASE}/jobs/${jobId}/artifacts/${name}`);
  return res.text();
}

export async function submitRerun(jobId: string): Promise<{ job_id: string; status: string }> {
  const res = await fetchWithAuth(`${API_BASE}/jobs/${jobId}/rerun`, { method: "POST" });
  return res.json();
}

export async function getJobHistory(jobId: string): Promise<{ history: JobSummary[] }> {
  const res = await fetchWithAuth(`${API_BASE}/jobs/${jobId}/history`);
  return res.json();
}

export async function getJobDiff(jobId: string, otherJobId: string): Promise<any> {
  const res = await fetchWithAuth(`${API_BASE}/jobs/${jobId}/diff/${otherJobId}`);
  return res.json();
}

// ---------------------------------------------------------------------------
// Auth logic
// ---------------------------------------------------------------------------

export async function loginUser(username: string, password: string): Promise<void> {
  const formData = new FormData();
  formData.append("username", username);
  formData.append("password", password);

  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    throw new Error("Login failed (check credentials)");
  }
}

export async function registerUser(username: string, password: string): Promise<void> {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || "Registration failed");
  }
}

export async function logoutUser(): Promise<void> {
  await fetch(`${API_BASE}/auth/logout`, { method: "POST" });
  if (typeof window !== "undefined") {
    window.location.href = "/login";
  }
}
