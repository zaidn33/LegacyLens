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
      {/* Background layers */}
      <div className={styles.bgImage} />
      <div className={styles.bgOverlay} />
      <div className={styles.bgGrid} />

      {/* Navbar */}
      <header className={styles.navbar}>
        <div className={styles.brand}>
          <span className={styles.dotRed} />
          <span className={styles.dotYellow} />
          <span className={styles.dotGreen} />
          <h1 className={styles.logoText}>LegacyLens</h1>
        </div>
        <button 
          onClick={() => logoutUser()} 
          className={styles.logoutBtn}
        >
          Logout
        </button>
      </header>

      <main className={styles.main}>
        {/* Hero Section */}
        <section className={styles.hero}>
          <h2 className={styles.heroTitle}>
            Modernize COBOL<br />to Python Automatically
          </h2>
          <p className={styles.heroSub}>
            Preserve business logic, maintain traceability, and accelerate your
            mainframe migration with intelligent code conversion.
          </p>

          {/* Code transformation visual */}
          <div className={styles.codeTransform}>
            <span className={styles.cobolPill}>
              <code>DISPLAY &quot;Hello&quot;</code>
            </span>
            <span className={styles.transformArrow}>→</span>
            <span className={styles.pythonPill}>
              <code>print(&quot;Hello&quot;)</code>
            </span>
          </div>
        </section>

        {/* Upload Section */}
        <section className={styles.uploadSection}>
          <div className={styles.uploadGlass}>
            <FileUpload onUpload={handleUpload} disabled={isUploading} />
            {error && <p className={styles.error}>{error}</p>}
          </div>
        </section>

        {/* How It Works */}
        <section className={styles.howSection}>
          <h3 className={styles.sectionTitle}>How It Works</h3>
          <div className={styles.stepsGrid}>
            <div className={styles.stepCard}>
              <div className={styles.stepIcon}>
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#ffffff" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                  <polyline points="14 2 14 8 20 8"/>
                  <line x1="12" y1="18" x2="12" y2="12"/>
                  <line x1="9" y1="15" x2="15" y2="15"/>
                </svg>
              </div>
              <span className={styles.stepNum}>01</span>
              <h4 className={styles.stepTitle}>Upload COBOL</h4>
              <p className={styles.stepDesc}>
                Drop your .cbl, .cob, or .cpy files. We parse every division, section, and paragraph.
              </p>
            </div>
            <div className={styles.stepCard}>
              <div className={styles.stepIcon}>
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#ffffff" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10"/>
                  <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
                  <circle cx="12" cy="17" r=".5"/>
                </svg>
              </div>
              <span className={styles.stepNum}>02</span>
              <h4 className={styles.stepTitle}>AI Analysis</h4>
              <p className={styles.stepDesc}>
                Our engine maps business rules, control flow, data structures, and edge cases.
              </p>
            </div>
            <div className={styles.stepCard}>
              <div className={styles.stepIcon}>
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#ffffff" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                  <polyline points="22 4 12 14.01 9 11.01"/>
                </svg>
              </div>
              <span className={styles.stepNum}>03</span>
              <h4 className={styles.stepTitle}>Get Python</h4>
              <p className={styles.stepDesc}>
                Download production-ready Python with full traceability back to original COBOL lines.
              </p>
            </div>
          </div>
        </section>

        {/* Enterprise-Grade Conversion */}
        <section className={styles.enterpriseSection}>
          <h3 className={styles.sectionTitle}>Enterprise-Grade Conversion</h3>
          <p className={styles.sectionSub}>
            Built for the complexity of real-world mainframe applications.
          </p>
          <div className={styles.featureGrid}>
            <div className={styles.featureCard}>
              <div className={styles.featureIcon}>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#ffffff" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                </svg>
              </div>
              <h4 className={styles.featureTitle}>Business Logic Preserved</h4>
              <p className={styles.featureDesc}>
                Every rule, condition, and calculation mapped with full fidelity.
              </p>
            </div>
            <div className={styles.featureCard}>
              <div className={styles.featureIcon}>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#ffffff" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
                </svg>
              </div>
              <h4 className={styles.featureTitle}>Fast Conversion</h4>
              <p className={styles.featureDesc}>
                Thousands of lines processed in seconds, not months of manual rewriting.
              </p>
            </div>
            <div className={styles.featureCard}>
              <div className={styles.featureIcon}>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#ffffff" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
                </svg>
              </div>
              <h4 className={styles.featureTitle}>Full Traceability</h4>
              <p className={styles.featureDesc}>
                Line-by-line mapping from COBOL source to Python output.
              </p>
            </div>
            <div className={styles.featureCard}>
              <div className={styles.featureIcon}>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#ffffff" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="18" y1="20" x2="18" y2="10"/>
                  <line x1="12" y1="20" x2="12" y2="4"/>
                  <line x1="6" y1="20" x2="6" y2="14"/>
                </svg>
              </div>
              <h4 className={styles.featureTitle}>Confidence Scoring</h4>
              <p className={styles.featureDesc}>
                AI-powered confidence metrics for every converted module.
              </p>
            </div>
          </div>
        </section>

        {/* Pipeline Runs */}
        <section className={styles.runsSection}>
          <div className={styles.runsHeader}>
            <h3 className={styles.runsTitle}>Pipeline Runs</h3>
            <span className={styles.runsCount}>{jobs.length} jobs</span>
          </div>
          <JobTable jobs={jobs} />
        </section>
      </main>
    </div>
  );
}
