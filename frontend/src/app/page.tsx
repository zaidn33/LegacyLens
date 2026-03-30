"use client";

import { useCallback, useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { submitJob, listJobs } from "@/lib/api";
import type { JobSummary } from "@/lib/types";
import FileUpload from "@/components/FileUpload";
import JobTable from "@/components/JobTable";
import styles from "./page.module.css";

export default function DashboardPage() {
  const router = useRouter();
  const [jobs, setJobs] = useState<JobSummary[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | undefined>(undefined);

  // Fetch jobs on mount + poll every 3s
  const fetchJobs = useCallback(async () => {
    try {
      const data = await listJobs(1, 50);
      setJobs(data.jobs);
    } catch {
      // Silently ignore fetch errors during polling
    }
  }, []);

  useEffect(() => {
    fetchJobs();
    pollRef.current = setInterval(fetchJobs, 3000);
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [fetchJobs]);

  const handleUpload = useCallback(
    async (file: File) => {
      setIsUploading(true);
      setError(null);
      try {
        const res = await submitJob(file);
        await fetchJobs();
        router.push(`/jobs/${res.job_id}`);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Upload failed");
      } finally {
        setIsUploading(false);
      }
    },
    [fetchJobs, router]
  );

  return (
    <div className={styles.page}>
      {/* Header */}
      <header className={styles.header}>
        <div className={styles.brand}>
          <span className={styles.logo}>◈</span>
          <h1 className={styles.title}>LegacyLens</h1>
          <span className={styles.tag}>Agentic Code Modernization</span>
        </div>
      </header>

      <main className={`container ${styles.main}`}>
        {/* Upload */}
        <section className={styles.uploadSection}>
          <FileUpload onUpload={handleUpload} disabled={isUploading} />
          {error && <p className={styles.error}>{error}</p>}
        </section>

        {/* Job List */}
        <section className={`card ${styles.listSection}`}>
          <div className={styles.listHeader}>
            <h2 className={styles.listTitle}>Pipeline Runs</h2>
            <span className={styles.listCount}>{jobs.length} jobs</span>
          </div>
          <JobTable jobs={jobs} />
        </section>
      </main>
    </div>
  );
}
