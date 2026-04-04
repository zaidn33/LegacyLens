"use client";

import { useCallback, useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { submitJob, listJobs, logoutUser, AuthError } from "@/lib/api";
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
    } catch (e) {
      if (e instanceof AuthError) {
        if (pollRef.current) clearInterval(pollRef.current);
      }
    }
  }, []);

  useEffect(() => {
    fetchJobs();
    pollRef.current = setInterval(fetchJobs, 3000);
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [fetchJobs]);

  const handleUpload = useCallback(
    async (file: File, dependencies?: File[]) => {
      setIsUploading(true);
      setError(null);
      try {
        const res = await submitJob(file, dependencies);
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
      <header className={styles.header}>
        <div className={styles.brand}>
          <span className={styles.logo}>👓</span>
          <h1 className={styles.title}>LegacyLens</h1>
        </div>
        <button 
          onClick={() => logoutUser()} 
          style={{ background: 'transparent', border: '1px solid var(--border-primary)', color: 'var(--text-primary)', padding: '0.4rem 1rem', borderRadius: '4px', cursor: 'pointer' }}
        >
          Logout
        </button>
      </header>

      <main className={`container ${styles.main}`}>
        {/* Hero Section */}
        <section className={styles.heroSection}>
          <h2 className={styles.heroTitle}>
            Modernize COBOL<br />to Python Automatically
          </h2>
          <p className={styles.heroDescription}>
            Preserve business logic, maintain traceability, and accelerate your mainframe migration with intelligent code conversion.
          </p>
          <div className={styles.codeBadge}>
            <span className={styles.pillCobol}>[COBOL]</span>
            <span className={styles.pillArrow}>→</span>
            <span className={styles.pillPython}>[Python]</span>
          </div>
        </section>

        {/* Upload */}
        <section className={styles.uploadSection}>
          <div className={styles.uploadWrapper}>
            <FileUpload onUpload={handleUpload} disabled={isUploading} />
            {error && <p className={styles.error}>{error}</p>}
          </div>
        </section>

        {/* Features */}
        <section className={styles.featuresSection}>
          <div className={styles.featureCard}>
            <span className={styles.featureIcon}>🧬</span>
            <h4>Logic Preservation</h4>
            <p>Maps native logic patterns explicitly before code generation.</p>
          </div>
          <div className={styles.featureCard}>
            <span className={styles.featureIcon}>📊</span>
            <h4>Full Traceability</h4>
            <p>Maintains parity records from mainframe source to target Python.</p>
          </div>
          <div className={styles.featureCard}>
            <span className={styles.featureIcon}>⚡</span>
            <h4>Intelligent Analysis</h4>
            <p>Uses multi-agent refinement for confident dependency resolution.</p>
          </div>
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
