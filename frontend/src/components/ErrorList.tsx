import type { PipelineError } from "@/lib/types";
import styles from "./ErrorList.module.css";

interface Props {
  errors: PipelineError[];
}

export default function ErrorList({ errors }: Props) {
  if (errors.length === 0) return null;

  return (
    <div className={styles.wrapper}>
      <h3 className={styles.title}>Pipeline Errors ({errors.length})</h3>
      {errors.map((err, i) => (
        <div key={i} className={styles.error}>
          <div className={styles.header}>
            <span className={styles.stage}>{err.stage}</span>
            <span className={styles.type}>{err.error_type}</span>
            {err.iteration !== null && (
              <span className={styles.iteration}>iter {err.iteration}</span>
            )}
            <span
              className={`${styles.recoverBadge} ${
                err.recoverable ? styles.recoverable : styles.nonrecoverable
              }`}
            >
              {err.recoverable ? "Recoverable" : "Non-recoverable"}
            </span>
          </div>
          <p className={styles.message}>{err.message}</p>
        </div>
      ))}
    </div>
  );
}
