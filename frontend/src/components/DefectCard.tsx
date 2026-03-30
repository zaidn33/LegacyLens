import type { Defect } from "@/lib/types";
import styles from "./DefectCard.module.css";

interface Props {
  defect: Defect;
}

export default function DefectCard({ defect }: Props) {
  const severityClass = styles[defect.severity] || styles.minor;
  return (
    <div className={`${styles.card} ${severityClass}`}>
      <div className={styles.header}>
        <span className={styles.severityBadge}>{defect.severity.toUpperCase()}</span>
        <span className={styles.logicStep}>{defect.logic_step}</span>
      </div>
      <p className={styles.description}>{defect.description}</p>
      {defect.suggested_fix && (
        <p className={styles.fix}>
          <strong>Fix: </strong>{defect.suggested_fix}
        </p>
      )}
    </div>
  );
}
