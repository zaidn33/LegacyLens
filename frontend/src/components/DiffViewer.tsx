"use client";

import type { DiffResponse } from "@/lib/types";
import styles from "./DiffViewer.module.css";

interface DiffViewerProps {
  diff: DiffResponse;
  onClose: () => void;
}

export default function DiffViewer({ diff, onClose }: DiffViewerProps) {
  return (
    <div className={styles.overlay}>
      <div className={styles.modal}>
        <div className={styles.header}>
          <h2 className={styles.title}>Version Comparison</h2>
          <button className={styles.closeBtn} onClick={onClose}>×</button>
        </div>
        
        <div className={styles.content}>
          <div className={styles.section}>
            <h3>Code Output</h3>
            <div className={styles.metricRow}>
              <div className={styles.metric}>
                <span>Lines Before</span>
                <strong>{diff.code_delta.lines_before}</strong>
              </div>
              <div className={styles.metric}>
                <span>Lines After</span>
                <strong>{diff.code_delta.lines_after}</strong>
              </div>
              <div className={styles.metric}>
                <span>Changed</span>
                <strong>{diff.code_delta.changed ? "Yes" : "No"}</strong>
              </div>
            </div>
            {diff.code_delta.changed_line_numbers.length > 0 && (
              <p className={styles.textSmall}>
                Changed line numbers: {diff.code_delta.changed_line_numbers.join(", ")}
              </p>
            )}
          </div>

          <div className={styles.section}>
            <h3>Logic Map</h3>
            <p className={styles.textMedium}>
              Status: {diff.logic_map_delta.changed ? "Modified" : "Unchanged"}
            </p>
            {diff.logic_map_delta.details && (
              <p className={styles.textSmall}>{diff.logic_map_delta.details}</p>
            )}
          </div>

          <div className={styles.section}>
            <h3>Reviewer Confidence</h3>
            <div className={styles.arrowCompare}>
              <span className={styles.badge}>{diff.confidence_delta.old_level || "N/A"}</span>
              <span className={styles.arrow}>→</span>
              <span className={styles.badge}>{diff.confidence_delta.new_level || "N/A"}</span>
            </div>
          </div>
          
          <div className={styles.section}>
            <h3>Reviewer Defects</h3>
            <div className={styles.arrowCompare}>
              <span className={styles.badgeCount}>{diff.defect_delta.old_count}</span>
              <span className={styles.arrow}>→</span>
              <span className={styles.badgeCount}>{diff.defect_delta.new_count}</span>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
