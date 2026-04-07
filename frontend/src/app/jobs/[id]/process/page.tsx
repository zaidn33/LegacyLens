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
