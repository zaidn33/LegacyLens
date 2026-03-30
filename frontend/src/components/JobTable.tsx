"use client";

import Link from "next/link";
import type { JobSummary } from "@/lib/types";
import StatusBadge from "./StatusBadge";
import ConfidenceBadge from "./ConfidenceBadge";
import styles from "./JobTable.module.css";

interface Props {
  jobs: JobSummary[];
}

function formatDate(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

export default function JobTable({ jobs }: Props) {
  if (jobs.length === 0) {
    return (
      <div className={styles.empty}>
        <p>No jobs yet. Upload a COBOL file to get started.</p>
      </div>
    );
  }

  return (
    <div className={styles.wrapper}>
      <table className={styles.table}>
        <thead>
          <tr>
            <th>File</th>
            <th>Status</th>
            <th>Confidence</th>
            <th>Iterations</th>
            <th>Created</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {jobs.map((job) => (
            <tr key={job.job_id} className={styles.row}>
              <td className={styles.fileName}>
                <span className={styles.fileIcon}>📄</span>
                {job.file_name}
              </td>
              <td>
                <StatusBadge status={job.status} />
              </td>
              <td>
                <ConfidenceBadge level={job.confidence_level} />
              </td>
              <td className={styles.mono}>{job.iterations}</td>
              <td className={styles.date}>{formatDate(job.created_at)}</td>
              <td>
                <Link href={`/jobs/${job.job_id}`} className={styles.viewLink}>
                  View →
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
