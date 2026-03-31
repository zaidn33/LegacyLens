"use client";

import Link from "next/link";
import type { JobSummary } from "@/lib/types";
import styles from "./VersionHistory.module.css";
import StatusBadge from "./StatusBadge";

interface VersionHistoryProps {
  currentJobId: string;
  history: JobSummary[];
  onCompare: (baseJobId: string) => void;
}

export default function VersionHistory({ currentJobId, history, onCompare }: VersionHistoryProps) {
  if (!history || history.length === 0) return null;

  return (
    <div className={styles.container}>
      <h3 className={styles.title}>Run History</h3>
      <div className={styles.timeline}>
        {history.map((job) => {
          const isCurrent = job.job_id === currentJobId;
          const date = new Date(job.created_at).toLocaleString();
          
          return (
            <div key={job.job_id} className={`${styles.item} ${isCurrent ? styles.active : ""}`}>
              <div className={styles.versionBubble}>v{job.run_version}</div>
              <div className={styles.content}>
                <div className={styles.header}>
                  <Link href={`/jobs/${job.job_id}`} className={styles.link}>
                    {date}
                  </Link>
                  {isCurrent && <span className={styles.currentBadge}>Current</span>}
                </div>
                <div className={styles.meta}>
                  <StatusBadge status={job.status} />
                  {job.has_errors && <span className={styles.errorIcon}>⚠</span>}
                </div>
                
                {!isCurrent && (
                  <button 
                    className={styles.compareBtn}
                    onClick={() => onCompare(job.job_id)}
                  >
                    Compare with Current
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
