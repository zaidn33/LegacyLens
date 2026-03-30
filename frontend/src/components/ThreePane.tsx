import styles from "./ThreePane.module.css";

interface Props {
  left: React.ReactNode;
  center: React.ReactNode;
  right: React.ReactNode;
}

export default function ThreePane({ left, center, right }: Props) {
  return (
    <div className={styles.grid}>
      <div className={styles.pane}>{left}</div>
      <div className={styles.pane}>{center}</div>
      <div className={styles.pane}>{right}</div>
    </div>
  );
}
