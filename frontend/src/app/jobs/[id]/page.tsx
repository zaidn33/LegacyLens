"use client";

import { useEffect, useState, useRef, use } from "react";
import { useRouter } from "next/navigation";
import { getJobStatus, getJobHistory, submitRerun, logoutUser, AuthError } from "@/lib/api";
import type { JobStatusResponse, JobSummary } from "@/lib/types";
import CodeViewer from "@/components/CodeViewer";
import StatusBadge from "@/components/StatusBadge";
import ConfidenceBadge from "@/components/ConfidenceBadge";
import Link from "next/link";
import styles from "./page.module.css";

export default function JobDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const router = useRouter();
  const [job, setJob] = useState<JobStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [isRerunning, setIsRerunning] = useState(false);
  const pollRef = useRef<ReturnType<typeof setInterval> | undefined>(undefined);

  useEffect(() => {
    let cancelled = false;

    async function fetchJob() {
      try {
        const data = await getJobStatus(id);
        if (!cancelled) {
          setJob(data);
          setLoading(false);
          if (
            ["completed", "completed_with_errors", "failed"].includes(
              data.status
            )
          ) {
            if (pollRef.current) clearInterval(pollRef.current);
          }
        }
      } catch (e) {
        if (e instanceof AuthError) {
          cancelled = true;
          if (pollRef.current) clearInterval(pollRef.current);
        } else if (!cancelled) {
          setLoading(false);
        }
      }
    }

    fetchJob();
    pollRef.current = setInterval(fetchJob, 2000);
    return () => {
      cancelled = true;
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [id]);

  async function handleRerun() {
    try {
      setIsRerunning(true);
      const res = await submitRerun(id);
      router.push(`/jobs/${res.job_id}`);
    } catch (e) {
      alert("Failed to rerun: " + e);
      setIsRerunning(false);
    }
  }

  if (loading) {
    return (
      <div className={styles.loadingPage}>
        <div className={styles.spinner} />
        <p>Loading job...</p>
      </div>
    );
  }

  if (!job) {
    return (
      <div className={styles.loadingPage}>
        <p>Job not found.</p>
        <Link href="/" className={styles.backLink}>
          ← Back to Dashboard
        </Link>
      </div>
    );
  }

  const result = job.result;
  const isTerminal = ["completed", "completed_with_errors", "failed"].includes(job.status);

  return (
    <div className={styles.page}>
      {/* Shooting stars background */}
      <div className={styles.starsContainer}>
        <div className={styles.shootingStar} style={{ top: '10%', left: '5%', animationDelay: '0s', animationDuration: '3s' }} />
        <div className={styles.shootingStar} style={{ top: '25%', left: '20%', animationDelay: '1.5s', animationDuration: '2.5s' }} />
        <div className={styles.shootingStar} style={{ top: '45%', left: '60%', animationDelay: '3s', animationDuration: '3.5s' }} />
        <div className={styles.shootingStar} style={{ top: '15%', left: '75%', animationDelay: '5s', animationDuration: '2s' }} />
        <div className={styles.shootingStar} style={{ top: '60%', left: '30%', animationDelay: '7s', animationDuration: '3s' }} />
        <div className={styles.shootingStar} style={{ top: '35%', left: '90%', animationDelay: '2s', animationDuration: '2.8s' }} />
        <div className={styles.shootingStar} style={{ top: '70%', left: '10%', animationDelay: '4.5s', animationDuration: '3.2s' }} />
        <div className={styles.shootingStar} style={{ top: '5%', left: '45%', animationDelay: '6s', animationDuration: '2.3s' }} />
      </div>
      <div className={styles.bgOverlay} />

      {/* Top bar */}
      <header className={styles.topBar}>
        <div className={styles.topBarLeft}>
          <Link href="/" className={styles.backLink}>
            ← Dashboard
          </Link>
          <div className={styles.divider} />
          <span className={styles.jobId}>{job.file_name}</span>
          <StatusBadge status={job.status} />
          {result?.final_confidence && (
            <ConfidenceBadge level={result.final_confidence.level} />
          )}
        </div>
        <div className={styles.topBarRight}>
          {isTerminal && (
            <Link href={`/jobs/${id}/process`} className={styles.processBtn}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10"/>
                <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
                <circle cx="12" cy="17" r=".5"/>
              </svg>
              Agent Process
            </Link>
          )}
          <button
            className={styles.rerunBtn}
            onClick={handleRerun}
            disabled={isRerunning || job.status === "processing" || job.status === "pending"}
          >
            {isRerunning ? "Queuing..." : "♻️ Re-run"}
          </button>
          <button
            onClick={() => logoutUser()}
            className={styles.logoutBtn}
          >
            Logout
          </button>
        </div>
      </header>

      {/* Processing state */}
      {job.status === "processing" && (
        <div className={styles.processingBanner}>
          <div className={styles.spinner} />
          <span>Pipeline is running...</span>
          {job.current_node && (
            <span className={styles.nodeLabel}>{job.current_node}</span>
          )}
          <span className={styles.iterLabel}>Iteration {job.iteration}</span>
        </div>
      )}

      {/* Two-pane code view */}
      <div className={styles.codeGrid}>
        {/* Source Code */}
        <div className={styles.codePane}>
          <div className={styles.codePaneHeader}>
            <div className={styles.windowDots}>
              <span className={styles.dot} style={{ background: '#ef4444' }} />
              <span className={styles.dot} style={{ background: '#eab308' }} />
              <span className={styles.dot} style={{ background: '#22c55e' }} />
            </div>
            <span className={styles.codePaneTitle}>SOURCE — COBOL</span>
            <span className={styles.codePaneFile}>{job.file_name}</span>
          </div>
          <div className={styles.codePaneBody}>
            {job.source_code ? (
              <CodeViewer code={job.source_code} language="cobol" />
            ) : (
              <p className={styles.noData}>No source code available</p>
            )}
          </div>
        </div>

        {/* Output Code */}
        <div className={styles.codePane}>
          <div className={styles.codePaneHeader}>
            <div className={styles.windowDots}>
              <span className={styles.dot} style={{ background: '#ef4444' }} />
              <span className={styles.dot} style={{ background: '#eab308' }} />
              <span className={styles.dot} style={{ background: '#22c55e' }} />
            </div>
            <span className={styles.codePaneTitle}>OUTPUT — PYTHON</span>
            <span className={styles.codePaneFile}>modernized.py</span>
          </div>
          <div className={styles.codePaneBody}>
            {result?.coder_output ? (
              <CodeViewer
                code={result.coder_output.generated_code}
                language="python"
              />
            ) : (
              <div className={styles.outputPending}>
                {job.status === "processing" ? (
                  <>
                    <div className={styles.spinnerLg} />
                    <p>Generating modernized code...</p>
                  </>
                ) : job.status === "failed" ? (
                  <>
                    <p className={styles.failedIcon}>✗</p>
                    <p>Pipeline failed</p>
                    {job.error && <p className={styles.errorText}>{job.error}</p>}
                  </>
                ) : (
                  <p className={styles.muted}>No output available</p>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Bottom stats bar */}
      {result && (
        <div className={styles.statsBar}>
          <div className={styles.stat}>
            <span className={styles.statLabel}>Source Lines</span>
            <span className={styles.statValue}>{job.source_code.split('\n').length}</span>
          </div>
          <div className={styles.stat}>
            <span className={styles.statLabel}>Output Lines</span>
            <span className={styles.statValue}>
              {result.coder_output ? result.coder_output.generated_code.split('\n').length : '—'}
            </span>
          </div>
          <div className={styles.stat}>
            <span className={styles.statLabel}>Confidence</span>
            <span className={styles.statValue}>
              {result.final_confidence ? result.final_confidence.level : '—'}
            </span>
          </div>
          <div className={styles.stat}>
            <span className={styles.statLabel}>Iterations</span>
            <span className={styles.statValue}>{result.iterations}</span>
          </div>
          <div className={styles.stat}>
            <span className={styles.statLabel}>Defects</span>
            <span className={styles.statValue}>
              {result.reviewer_output ? result.reviewer_output.defects.length : '—'}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
