import styles from "./ConfidenceBadge.module.css";

interface Props {
  level: string | null;
}

export default function ConfidenceBadge({ level }: Props) {
  if (!level) return <span className={`${styles.badge} ${styles.none}`}>—</span>;

  const cls = styles[level.toLowerCase()] || styles.none;
  return <span className={`${styles.badge} ${cls}`}>{level}</span>;
}
