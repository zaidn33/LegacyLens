"use client";

import { useEffect, useState, useRef, use } from "react";
import { useRouter } from "next/navigation";
import { getJobStatus, getJobHistory, getJobDiff, logoutUser, AuthError } from "@/lib/api";
import type { JobStatusResponse, JobSummary, DiffResponse } from "@/lib/types";
import TabPanel from "@/components/TabPanel";
import CodeViewer from "@/components/CodeViewer";
import LogicMapView from "@/components/LogicMapView";
import DefectCard from "@/components/DefectCard";
import ErrorList from "@/components/ErrorList";
import StatusBadge from "@/components/StatusBadge";
import ConfidenceBadge from "@/components/ConfidenceBadge";
import VersionHistory from "@/components/VersionHistory";
import DiffViewer from "@/components/DiffViewer";
import Link from "next/link";
import styles from "./process.module.css";

export default function ProcessPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const [job, setJob] = useState<JobStatusResponse | null>(null);
  const [history, setHistory] = useState<JobSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [diffData, setDiffData] = useState<DiffResponse | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | undefined>(undefined);

  useEffect(() => {
    let cancelled = false;

    async function fetchJob() {
      try {
        const data = await getJobStatus(id);
        if (!cancelled) {
          setJob(data);
          setLoading(false);
          if (["completed", "completed_with_errors", "failed"].includes(data.status)) {
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

    async function fetchHistory() {
      try {
        const h = await getJobHistory(id);
        if (!cancelled && h.history) {
          setHistory(h.history);
        }
      } catch (e) {
        if (e instanceof AuthError) {
          cancelled = true;
        }
      }
    }

    fetchJob();
    fetchHistory();
    pollRef.current = setInterval(fetchJob, 2000);
    return () => {
      cancelled = true;
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [id]);

  async function handleCompare(otherJobId: string) {
    try {
      const d = await getJobDiff(id, otherJobId);
      setDiffData(d);
    } catch (e: any) {
      alert("Failed to compute diff: " + e.message);
    }
  }

  if (loading) {
    return (
      <div className={styles.loadingPage}>
        <div className={styles.spinner} />
        <p>Loading...</p>
      </div>
    );
  }

  if (!job) {
    return (
      <div className={styles.loadingPage}>
        <p>Job not found.</p>
      </div>
    );
  }

  const result = job.result;

  // Build tabs
  const tabs = [];

  // Logic Map
  if (result?.logic_map) {
    tabs.push({
      id: "logicmap",
      label: "Logic Map",
      content: <LogicMapView logicMap={result.logic_map} />,
    });
  }

  // Review
  if (result?.reviewer_output) {
    const ro = result.reviewer_output;
    tabs.push({
      id: "review",
      label: `Review ${ro.passed ? "✓" : "✗"}`,
      content: (
        <div className={styles.section}>
          <div className={styles.reviewMeta}>
            <span>
              Passed: <strong>{ro.passed ? "Yes" : "No"}</strong>
            </span>
            <ConfidenceBadge level={ro.confidence.level} />
          </div>
          <h4 className={styles.subHeading}>Logic Parity Findings</h4>
          <p className={styles.bodyText}>{ro.logic_parity_findings}</p>
          {ro.defects.length > 0 && (
            <>
              <h4 className={styles.subHeading}>
                Defects ({ro.defects.length})
              </h4>
              {ro.defects.map((d, i) => (
                <DefectCard key={i} defect={d} />
              ))}
            </>
          )}
          {ro.known_limitations.length > 0 && (
            <>
              <h4 className={styles.subHeading}>Known Limitations</h4>
              <ul className={styles.limitationList}>
                {ro.known_limitations.map((l, i) => (
                  <li key={i}>{l}</li>
                ))}
              </ul>
            </>
          )}
        </div>
      ),
    });
  }

  // Confidence
  if (result?.final_confidence) {
    tabs.push({
      id: "confidence",
      label: "Confidence",
      content: (
        <div className={styles.section}>
          <div className={styles.confidenceLevel}>
            <ConfidenceBadge level={result.final_confidence.level} />
            <span className={styles.iterCount}>
              {result.iterations} iteration(s)
            </span>
          </div>
          <p className={styles.bodyText}>{result.final_confidence.rationale}</p>
        </div>
      ),
    });
  }

  // Tests
  if (result?.coder_output) {
    const co = result.coder_output;
    tabs.push({
      id: "tests",
      label: "Tests",
      content: <CodeViewer code={co.generated_tests} language="python" title="test_modernized.py" />,
    });

    if (co.logic_step_mapping.length > 0) {
      tabs.push({
        id: "mapping",
        label: "Mapping",
        content: (
          <div className={styles.mappingContent}>
            <table className={styles.mappingTable}>
              <thead>
                <tr>
                  <th>Function / Test</th>
                  <th>Logic Step</th>
                  <th>Notes</th>
                </tr>
              </thead>
              <tbody>
                {co.logic_step_mapping.map((m, i) => (
                  <tr key={i}>
                    <td className={styles.mono}>{m.function_or_test_name}</td>
                    <td>{m.logic_step}</td>
                    <td className={styles.muted}>{m.notes}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ),
      });
    }
  }

  // History
  if (history.length > 1) {
    tabs.push({
      id: "versions",
      label: `History (${history.length})`,
      content: <VersionHistory currentJobId={id} history={history} onCompare={handleCompare} />,
    });
  }

  // Errors
  if (job.errors.length > 0 || (result && result.errors.length > 0)) {
    tabs.push({
      id: "errors",
      label: `Errors (${(result?.errors || job.errors).length})`,
      content: <ErrorList errors={result?.errors || job.errors} />,
    });
  }

  if (tabs.length === 0) {
    tabs.push({
      id: "status",
      label: "Status",
      content: (
        <div className={styles.emptyState}>
          <StatusBadge status={job.status} />
          {job.error && <p className={styles.errorText}>{job.error}</p>}
        </div>
      ),
    });
  }

  return (
    <div className={styles.page}>
      {/* Background layers */}
      <div className={styles.bgImage} />
      {/* Shooting stars */}
      <div className={styles.starsContainer}>
        {/* Original 8 stars */}
        <div className={styles.shootingStar} style={{ top: '6%', left: '5%', animationDelay: '0s', animationDuration: '4.5s' }} />
        <div className={styles.shootingStar} style={{ top: '20%', left: '25%', animationDelay: '2.5s', animationDuration: '3.8s' }} />
        <div className={styles.shootingStar} style={{ top: '45%', left: '60%', animationDelay: '5s', animationDuration: '4s' }} />
        <div className={styles.shootingStar} style={{ top: '14%', left: '80%', animationDelay: '7.5s', animationDuration: '3.2s' }} />
        <div className={styles.shootingStar} style={{ top: '55%', left: '15%', animationDelay: '9s', animationDuration: '5s' }} />
        <div className={styles.shootingStar} style={{ top: '35%', left: '90%', animationDelay: '3.5s', animationDuration: '4.2s' }} />
        <div className={styles.shootingStar} style={{ top: '70%', left: '40%', animationDelay: '6.5s', animationDuration: '3.5s' }} />
        <div className={styles.shootingStar} style={{ top: '8%', left: '50%', animationDelay: '1.5s', animationDuration: '5.5s' }} />
        {/* Additional 12 stars */}
        <div className={styles.shootingStar} style={{ top: '28%', left: '10%', animationDelay: '0.8s', animationDuration: '4.1s' }} />
        <div className={styles.shootingStar} style={{ top: '82%', left: '85%', animationDelay: '4.3s', animationDuration: '5.2s' }} />
        <div className={styles.shootingStar} style={{ top: '52%', left: '38%', animationDelay: '8.8s', animationDuration: '3.7s' }} />
        <div className={styles.shootingStar} style={{ top: '25%', left: '55%', animationDelay: '1.2s', animationDuration: '4.8s' }} />
        <div className={styles.shootingStar} style={{ top: '90%', left: '25%', animationDelay: '5.7s', animationDuration: '3.9s' }} />
        <div className={styles.shootingStar} style={{ top: '10%', left: '95%', animationDelay: '3.1s', animationDuration: '4.3s' }} />
        <div className={styles.shootingStar} style={{ top: '65%', left: '5%', animationDelay: '7.9s', animationDuration: '5.1s' }} />
        <div className={styles.shootingStar} style={{ top: '45%', left: '85%', animationDelay: '2.4s', animationDuration: '3.4s' }} />
        <div className={styles.shootingStar} style={{ top: '75%', left: '70%', animationDelay: '9.5s', animationDuration: '4.6s' }} />
        <div className={styles.shootingStar} style={{ top: '15%', left: '40%', animationDelay: '4.8s', animationDuration: '3.6s' }} />
        <div className={styles.shootingStar} style={{ top: '60%', left: '55%', animationDelay: '6.1s', animationDuration: '4.9s' }} />
        <div className={styles.shootingStar} style={{ top: '35%', left: '75%', animationDelay: '8.4s', animationDuration: '4.4s' }} />
      </div>
      <div className={styles.bgOverlay} />

      <header className={styles.topBar}>
        <div className={styles.topBarLeft}>
          <Link href={`/jobs/${id}`} className={styles.backLink}>
            ← Back to Code View
          </Link>
          <div className={styles.divider} />
          <span className={styles.jobId}>Agent Process</span>
          <StatusBadge status={job.status} />
        </div>
        <div className={styles.topBarRight}>
          <button onClick={() => logoutUser()} className={styles.logoutBtn}>
            Logout
          </button>
        </div>
      </header>

      <main className={styles.main}>
        <TabPanel tabs={tabs} defaultTab="logicmap" />
      </main>

      {diffData && (
        <DiffViewer diff={diffData} onClose={() => setDiffData(null)} />
      )}
    </div>
  );
}
