import styles from "./StatusBadge.module.css";

interface Props {
  status: string;
}

const STATUS_LABELS: Record<string, string> = {
  pending: "Pending",
  processing: "Processing",
  completed: "Completed",
  completed_with_errors: "Partial",
  failed: "Failed",
};

export default function StatusBadge({ status }: Props) {
  const label = STATUS_LABELS[status] || status;
  const cls = styles[status.replace(/_/g, "")] || styles.pending;

  return (
    <span className={`${styles.badge} ${cls}`}>
      {status === "processing" && <span className={styles.dot} />}
      {label}
    </span>
  );
}
