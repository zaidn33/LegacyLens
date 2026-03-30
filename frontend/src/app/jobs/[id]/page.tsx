"use client";

import { useEffect, useState, useRef, use } from "react";
import Link from "next/link";
import { getJobStatus } from "@/lib/api";
import type { JobStatusResponse } from "@/lib/types";
import ThreePane from "@/components/ThreePane";
import TabPanel from "@/components/TabPanel";
import CodeViewer from "@/components/CodeViewer";
import LogicMapView from "@/components/LogicMapView";
import DefectCard from "@/components/DefectCard";
import ErrorList from "@/components/ErrorList";
import StatusBadge from "@/components/StatusBadge";
import ConfidenceBadge from "@/components/ConfidenceBadge";
import styles from "./page.module.css";

function StageMissing({ stage }: { stage: string }) {
  return (
    <div className={styles.missing}>
      <p className={styles.missingIcon}>⚠</p>
      <p className={styles.missingTitle}>Stage did not complete</p>
      <p className={styles.missingText}>
        The <strong>{stage}</strong> stage did not produce output. Check the
        Errors tab for details.
      </p>
    </div>
  );
}

export default function JobDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const [job, setJob] = useState<JobStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const pollRef = useRef<ReturnType<typeof setInterval> | undefined>(undefined);

  useEffect(() => {
    let cancelled = false;

    async function fetchJob() {
      try {
        const data = await getJobStatus(id);
        if (!cancelled) {
          setJob(data);
          setLoading(false);

          // Stop polling once terminal state reached
          if (
            ["completed", "completed_with_errors", "failed"].includes(
              data.status
            )
          ) {
            if (pollRef.current) clearInterval(pollRef.current);
          }
        }
      } catch {
        if (!cancelled) setLoading(false);
      }
    }

    fetchJob();
    pollRef.current = setInterval(fetchJob, 2000);

    return () => {
      cancelled = true;
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [id]);

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

  // --- Left pane: Source Code ---
  const leftPane = (
    <div className={styles.paneInner}>
      <div className={styles.paneHeader}>
        <span className={styles.paneTitle}>Source Code</span>
        <span className={styles.mono}>{job.file_name}</span>
      </div>
      {job.source_code ? (
        <CodeViewer code={job.source_code} language="cobol" title={job.file_name} />
      ) : (
        <p className={styles.noData}>No source code available</p>
      )}
    </div>
  );

  // --- Center pane: Agent Process ---
  const centerTabs = [];

  if (result?.logic_map) {
    centerTabs.push({
      id: "logicmap",
      label: "Logic Map",
      content: <LogicMapView logicMap={result.logic_map} />,
    });
  }

  if (result?.reviewer_output) {
    const ro = result.reviewer_output;
    centerTabs.push({
      id: "review",
      label: `Review ${ro.passed ? "✓" : "✗"}`,
      content: (
        <div className={styles.reviewContent}>
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
  } else if (
    result &&
    ["completed_with_errors", "failed"].includes(job.status)
  ) {
    centerTabs.push({
      id: "review",
      label: "Review",
      content: <StageMissing stage="Reviewer" />,
    });
  }

  // Errors tab — only if errors exist
  if (job.errors.length > 0 || (result && result.errors.length > 0)) {
    centerTabs.push({
      id: "errors",
      label: `Errors (${(result?.errors || job.errors).length})`,
      content: <ErrorList errors={result?.errors || job.errors} />,
    });
  }

  // Confidence tab
  if (result?.final_confidence) {
    centerTabs.push({
      id: "confidence",
      label: "Confidence",
      content: (
        <div className={styles.confidenceContent}>
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

  // Processing state
  if (centerTabs.length === 0) {
    centerTabs.push({
      id: "status",
      label: "Status",
      content: (
        <div className={styles.processingState}>
          {job.status === "processing" ? (
            <>
              <div className={styles.spinner} />
              <p>Pipeline is running...</p>
              {job.current_node && (
                <p className={styles.mono}>
                  Current node: {job.current_node}
                </p>
              )}
              <p className={styles.mono}>Iteration: {job.iteration}</p>
            </>
          ) : (
            <>
              <p>
                Status: <StatusBadge status={job.status} />
              </p>
              {job.error && <p className={styles.errorText}>{job.error}</p>}
            </>
          )}
        </div>
      ),
    });
  }

  const centerPane = (
    <div className={styles.paneInner}>
      <div className={styles.paneHeader}>
        <span className={styles.paneTitle}>Agent Process</span>
        <StatusBadge status={job.status} />
      </div>
      <TabPanel tabs={centerTabs} />
    </div>
  );

  // --- Right pane: Modernized Output ---
  const rightTabs = [];

  if (result?.coder_output) {
    const co = result.coder_output;
    rightTabs.push({
      id: "code",
      label: "Code",
      content: (
        <CodeViewer
          code={co.generated_code}
          language="python"
          title="modernized.py"
        />
      ),
    });
    rightTabs.push({
      id: "tests",
      label: "Tests",
      content: (
        <CodeViewer
          code={co.generated_tests}
          language="python"
          title="test_modernized.py"
        />
      ),
    });
    if (co.logic_step_mapping.length > 0) {
      rightTabs.push({
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
                    <td className={styles.mono}>
                      {m.function_or_test_name}
                    </td>
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
  } else if (
    result &&
    ["completed_with_errors", "failed"].includes(job.status)
  ) {
    rightTabs.push({
      id: "code",
      label: "Code",
      content: <StageMissing stage="Coder" />,
    });
  }

  if (rightTabs.length === 0) {
    rightTabs.push({
      id: "pending",
      label: "Output",
      content: (
        <div className={styles.processingState}>
          <p className={styles.muted}>
            {job.status === "processing"
              ? "Waiting for pipeline output..."
              : "No output available."}
          </p>
        </div>
      ),
    });
  }

  const rightPane = (
    <div className={styles.paneInner}>
      <div className={styles.paneHeader}>
        <span className={styles.paneTitle}>Modernized Output</span>
      </div>
      <TabPanel tabs={rightTabs} />
    </div>
  );

  return (
    <div className={styles.page}>
      {/* Top bar */}
      <header className={styles.topBar}>
        <Link href="/" className={styles.backLink}>
          ← Dashboard
        </Link>
        <span className={styles.jobId}>Job: {id.slice(0, 8)}...</span>
      </header>

      <ThreePane left={leftPane} center={centerPane} right={rightPane} />
    </div>
  );
}
