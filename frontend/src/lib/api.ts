/**
 * API client functions for the LegacyLens backend.
 */

import type { JobListResponse, JobStatusResponse, JobSummary, DiffResponse } from "./types";

const API_BASE = "http://localhost:8000/api/v1";

export async function submitJob(file: File, dependencies?: File[]): Promise<{ job_id: string; status: string }> {
  const formData = new FormData();
  formData.append("file", file);
  
  if (dependencies) {
    dependencies.forEach((dep) => {
      formData.append("dependencies", dep);
    });
  }

  const res = await fetch(`${API_BASE}/jobs`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    throw new Error(`Submit failed: ${res.status} ${res.statusText}`);
  }

  return res.json();
}

export async function listJobs(page = 1, limit = 20): Promise<JobListResponse> {
  const res = await fetch(`${API_BASE}/jobs?page=${page}&limit=${limit}`);
  if (!res.ok) {
    throw new Error(`List jobs failed: ${res.status}`);
  }
  return res.json();
}

export async function getJobStatus(jobId: string): Promise<JobStatusResponse> {
  const res = await fetch(`${API_BASE}/jobs/${jobId}`);
  if (!res.ok) {
    throw new Error(`Get job failed: ${res.status}`);
  }
  return res.json();
}

export async function getArtifact(jobId: string, name: string): Promise<string> {
  const res = await fetch(`${API_BASE}/jobs/${jobId}/artifacts/${name}`);
  if (!res.ok) {
    throw new Error(`Artifact not available: ${res.status}`);
  }
  return res.text();
}

export async function submitRerun(jobId: string): Promise<{ job_id: string; status: string }> {
  const res = await fetch(`${API_BASE}/jobs/${jobId}/rerun`, {
    method: "POST",
  });
  if (!res.ok) {
    throw new Error(`Rerun failed: ${res.status}`);
  }
  return res.json();
}

export async function getJobHistory(jobId: string): Promise<{ history: JobSummary[] }> {
  const res = await fetch(`${API_BASE}/jobs/${jobId}/history`);
  if (!res.ok) {
    throw new Error(`History failed: ${res.status}`);
  }
  return res.json();
}

export async function getJobDiff(jobId: string, otherJobId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/jobs/${jobId}/diff/${otherJobId}`);
  if (!res.ok) {
    throw new Error(`Diff failed: ${res.status}`);
  }
  return res.json();
}
